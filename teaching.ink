inkling "2.0"
using Math
using Goal

const bonsai_agent_num: number<0 .. 4 step 1> = 0

# Define a type that represents the per-iteration state
# returned by the simulator.
type SimState {
    # Number of items in inventory for each player.
    inventory_levels: number[4],
    # Number of items in customer orders for each player.
    customer_orders_to_be_filled: number[4],
    # Number of items in outstanding to supplier for each player.
    supplier_orders_to_be_delivered: number[4],
    # Number of items on the way for each player.
    arriving_shipments: number[4],
    # Number of orders on the way for each player.
    arriving_orders: number[4],
    # Current costs for each player.
    current_costs: number[4],
    # Total costs for each player.
    total_costs: number[4],
    # Costs for all players combined.
    cumulative_costs: number,
    # Number of items delivered to customers.
    total_delivered: number,
    # Number of items to be delivered to customers.
    outstanding_demand: number,
    # Current time in the simulation.
    time: number,
}

const AgentTypes: string<"bonsai", "bs", "random", "strm">[4] = ["bonsai", "random", "random", "random"]

# Define a type that represents the per-iteration action
# accepted by the simulator.
type Action {
    # The number of items to order for the Bonsai agent.
    order: number<0 .. 10 step 1>,
}

# Per-episode configuration that can be sent to the simulator.
# All iterations within an episode will use the same configuration.
type SimConfig {
    # The type of demand curve used, uniform or normal.
    demand_distribution: string,
    # Minimum number of demand per timestep, used with uniform distribution.
    demand_low: number<0 .. 5 step 1>,
    # Maximum number of demand per timestep, used with uniform distribution.
    demand_high: number<0 .. 100 step 1>,
    # The mu of the normal distribution for demand.
    demand_mu: number<0 .. 20 step 1>,
    # The sigma of the normal distribution for demand.
    demand_sigma: number<0 .. 10 step 1>,
    # Factor influencing the max order (action).
    action_high: number<0 .. 100 step 1>,
    # List of types of agents, defaults [bonsai, strm, strm, strm], other options are bs and random.
    agent_types: string<"bonsai", "bs", "random", "strm">[4],
    # Shortage costs per player.
    costs_shortage: number<0 .. 100 step 0.1>[4],
    # Holding costs per player.
    costs_holding: number<0 .. 100 step 0.1>[4],
    # Alpha of Sterman formula for each player, only used if the player uses Sterman.
    strm_alpha: number<-10 .. 10 step 0.1>[4],
    # Beta of Sterman formula for each player, only used if the player uses Sterman.
    strm_beta: number<-10 .. 10 step 0.1>[4],
    # The min lead time for receiving items per player.
    leadtime_receiving_low: number<0 .. 100 step 1>[4],
    # The max lead time for receiving items per player.
    leadtime_receiving_high: number<0 .. 100 step 1>[4],
    # The min lead time for receiving orders per player.
    leadtime_orders_low: number<0 .. 100 step 1>[4],
    # The max lead time for receiving orders per player.
    leadtime_orders_high: number<0 .. 100 step 1>[4],
    # The initial inventory.
    inventory_initial: number<0 .. 100 step 1>[4],
    # The initial number of arriving orders.
    arriving_orders_initial: number<0 .. 100 step 1>[4],
    # The initial number of arriving shipments.
    arriving_shipments_initial: number<0 .. 100 step 1>[4],
}

type ObservableState {
    # Number of items in inventory for each player.
    inventory_level: number,
    # Number of items in customer orders for each player.
    customer_orders_to_be_filled: number,
    # Number of items in outstanding to supplier for each player.
    supplier_orders_to_be_delivered: number,
    # Number of items on the way for each player.
    arriving_shipments: number,
    # Number of orders on the way for each player.
    arriving_orders: number,
    # Current costs for each player.
    current_costs: number,
    # Total costs for each player.
    total_costs: number,
    # Current time in the simulation.
    time: number,
}

function SpecifyState(s: SimState): ObservableState {
    return {
        inventory_level: s.inventory_levels[bonsai_agent_num],
        customer_orders_to_be_filled: s.customer_orders_to_be_filled[bonsai_agent_num],
        supplier_orders_to_be_delivered: s.supplier_orders_to_be_delivered[bonsai_agent_num],
        arriving_shipments: s.arriving_shipments[bonsai_agent_num],
        arriving_orders: s.arriving_orders[bonsai_agent_num],
        current_costs: s.current_costs[bonsai_agent_num],
        total_costs: s.total_costs[bonsai_agent_num],
        time: s.time
    }
}


simulator Simulator(action: Action, config: SimConfig): SimState {
}

# Define a concept graph
graph (input: SimState): Action {

    concept Specify(input): ObservableState {
        programmed SpecifyState
    }

    concept InitialTraining(Specify): Action {
        curriculum {
            source Simulator

            training {
                EpisodeIterationLimit: 100,
                TotalIterationLimit: 1000,
                NoProgressIterationLimit: 30
            }
            goal (state: SimState, action: Action) {
                # minimize costs:
                #     SimState.current_costs[0]
                #     in Goal.RangeBelow(10)
                minimize orders:
                    action.order
                    in Goal.RangeBelow(10)
                drive costs_down:
                    state.current_costs[bonsai_agent_num]
                    in Goal.Range(0, 10)
                # drive inventory:
                #     state.inventory_levels[bonsai_agent_num] in Goal.Range(5,15)
                # minimize backorders:
                #     state.customer_orders_to_be_filled[bonsai_agent_num] in Goal.RangeBelow(10)            
            }

            lesson `Lesson 1` {

                training {
                    LessonAssessmentWindow: 20
                }

            }
        }
    }

    output InitialTraining

}
