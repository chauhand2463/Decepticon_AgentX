from langgraph.graph import START, MessagesState, StateGraph
from langgraph.pregel import Pregel
from typing_extensions import (
    Any,
    Literal,
    Optional,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
)

from src.utils.swarm.handoff import get_handoff_destinations


class SwarmState(MessagesState):
    active_agent: Optional[str]


StateSchema = TypeVar("StateSchema", bound=SwarmState)
StateSchemaType = Type[StateSchema]


def _update_state_schema_agent_names(
    state_schema: StateSchemaType, agent_names: list[str]
) -> StateSchemaType:

    active_agent_annotation = state_schema.__annotations__["active_agent"]

    is_str_type = active_agent_annotation is str
    is_optional_str = (
        get_origin(active_agent_annotation) is Union
        and get_args(active_agent_annotation)[0] is str
    )

    if not (is_str_type or is_optional_str):
        return state_schema

    updated_schema = type(
        f"{state_schema.__name__}",
        (state_schema,),
        {"__annotations__": {**state_schema.__annotations__}},
    )

    literal_type = Literal.__getitem__(tuple(agent_names))

    if is_optional_str:
        updated_schema.__annotations__["active_agent"] = Optional[literal_type]
    else:
        updated_schema.__annotations__["active_agent"] = literal_type

    return updated_schema


def add_active_agent_router(
    builder: StateGraph,
    *,
    route_to: list[str],
    default_active_agent: str,
) -> StateGraph:

    if "active_agent" not in builder.channels:
        raise ValueError(
            "Missing required key 'active_agent' in in builder's state_schema"
        )

    if default_active_agent not in route_to:
        raise ValueError(
            f"Default active agent '{default_active_agent}' not found in routes {route_to}"
        )

    def route_to_active_agent(state: dict):
        return state.get("active_agent", default_active_agent)

    builder.add_conditional_edges(START, route_to_active_agent, path_map=route_to)
    return builder


def create_swarm(
    agents: list[Pregel],
    *,
    default_active_agent: str,
    state_schema: StateSchemaType = SwarmState,
    config_schema: Type[Any] | None = None,
) -> StateGraph:

    active_agent_annotation = state_schema.__annotations__.get("active_agent")
    if active_agent_annotation is None:
        raise ValueError("Missing required key 'active_agent' in state_schema")

    agent_names = [agent.name for agent in agents]
    state_schema = _update_state_schema_agent_names(state_schema, agent_names)
    builder = StateGraph(state_schema, config_schema)
    add_active_agent_router(
        builder,
        route_to=agent_names,
        default_active_agent=default_active_agent,
    )
    for agent in agents:
        builder.add_node(
            agent.name,
            agent,
            destinations=tuple(get_handoff_destinations(agent)),
        )

    return builder
