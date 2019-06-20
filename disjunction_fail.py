#!/usr/bin/env python3
from six.moves import xrange
from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2
from functools import partial
from itertools import chain
import argparse
import numpy as np

def vehicle_dummy_nodes(data):
    """slot in a dummy node for this vehicle.  Must go to dummy node from depot"""
    matrix = data['distance_matrix']
    regular_nodes = range(1,len(data['demands']))
    new_node = len(matrix[0])
    # distance from depot to new node is 0, from new node to all other
    # nodes is 0, but only given vehicle can fisit new node
    for rowidx in range(len(matrix)):
        row = matrix[rowidx]

        if rowidx == 0:
            # fix up first row
            for node in regular_nodes:
                row[node] = 1
            row.append(0) # free to get from depot to dummy node
        else:
            row.append(10000) # discourage trip to dummy nodes from dummy nodes

        matrix[rowidx] = row
    new_row = list(10000*np.ones_like(matrix[0]))
    new_row[0] = 0 # free to get from new node back to depot
    for node in regular_nodes:
        new_row[node] = 3 # just like regular depot to node cost
    matrix.append(new_row)
    data['distance_matrix'] = matrix
    return new_node

def vehicle_node_constraints(node, vehnum, routing, manager):
    idx = manager.NodeToIndex(node)


def create_data_model(args):
    """Stores the data for the problem."""
    data = {}
    if args.size4:
        data['distance_matrix'] = [
            [0, 3, 3, 3, 3],
            [3, 0, 1, 1, 1],
            [3, 1, 0, 1, 1],
            [3, 1, 1, 0, 1],
            [3, 1, 1, 1, 0]
        ]
        data['demands'] = [0, 1, 1, 1, 1 ]
    elif args.size7:
        data['distance_matrix'] = [
            [0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
            [3, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [3, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [3, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1],
            [3, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1],
            [3, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1],
            [3, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1],
            [3, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1],
            [3, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1],
            [3, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1],
            [3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1],
            [3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]
        ]
        data['demands'] = [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1 ]

    else:
        data['distance_matrix'] = [
            [0, 3, 3, 3, 3, 3],
            [3, 0, 1, 1, 1, 1],
            [3, 1, 0, 1, 1, 1],
            [3, 1, 1, 0, 1, 1],
            [3, 1, 1, 1, 0, 1],
            [3, 1, 1, 1, 1, 0]
        ]
        data['demands'] = [0, 1, 1, 1, 1, 1 ]

    data['vehicle_capacities'] = list(
        chain.from_iterable([args.combo_capacity,
                                args.single_capacity]
                               for _ in range(0,args.vehicles))
    )

    data['vehicle_costs'] = list(
        chain.from_iterable([args.combo_cost,
                                args.single_cost]
                               for _ in range(0,args.vehicles))
    )
    data['depot'] = 0
    return data


def print_solution(data, manager, routing, assignment):
    """Prints assignment on console."""
    total_distance = 0
    total_load = 0
    num_demand_nodes = len(data['demands'])
    countd = routing.GetDimensionOrDie('count')
    for vehicle_id in range(0,len(data['vehicle_costs'])):
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        route_distance = 0
        route_load = 0
        arc_cost = 0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            load = 0
            if node_index < num_demand_nodes:
                load = data['demands'][node_index]
            route_load += load
            plan_output += ' {0} Load({1}) Cost({2}) Count({3})-> '.format(node_index, route_load, arc_cost, assignment.Value(countd.CumulVar(index)))
            previous_index = index
            index = assignment.Value(routing.NextVar(index))
            arc_cost = routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
            route_distance += arc_cost
        plan_output += ' {0} Load({1}) Cost({2}) Count({3})\n'.format(
            manager.IndexToNode(index), route_load, arc_cost, assignment.Value(countd.CumulVar(index)))
        plan_output += 'Distance of the route: {}m\n'.format(route_distance)
        plan_output += 'Load of the route: {}\n'.format(route_load)
        print(plan_output)
        total_distance += route_distance
        total_load += route_load
    print('Total distance of all routes: {}m'.format(total_distance))
    print('Total load of all routes: {}'.format(total_load))

# Create and register a transit callback.
def distance_callback(data, manager, from_index, to_index):
    """Returns the distance between the two nodes."""
    # Convert from routing variable Index to distance matrix NodeIndex.
    from_node = manager.IndexToNode(from_index)
    to_node = manager.IndexToNode(to_index)
    return data['distance_matrix'][from_node][to_node]

def vehicle_distance_callback(data, vehicle, manager, from_index, to_index):
    """Returns the distance between the two nodes for a vehicle."""
    # Convert from routing variable Index to distance matrix NodeIndex.
    from_node = manager.IndexToNode(from_index)
    to_node = manager.IndexToNode(to_index)
    # print(from_node,to_node,data['distance_matrix'][from_node][to_node]*data['vehicle_costs'][vehicle])
    return data['distance_matrix'][from_node][to_node]*data['vehicle_costs'][vehicle]

def demand_callback(data, manager,from_index):
    """Returns the demand of the node."""
    # Convert from routing variable Index to demands NodeIndex.
    from_node = manager.IndexToNode(from_index)
    if from_node < len( data['demands'] ):
        return data['demands'][from_node]
    return 0


def main():
    parser = argparse.ArgumentParser(description='Play around with various options relating to disjunctions')
    parser.add_argument('-d,--disjunctions', action='store_true', dest='single_disjunctions',
                        default=False,
                        help='whether or not to use the single-node disjunctions')
    parser.add_argument('--singlepenalty', type=int, dest='singlepenalty', default=1,
                        help='penalty value to use for single element disjunction')
    parser.add_argument('-l,--log_search', action='store_true', dest='log_search',
                        default=False,
                        help='whether or not to output the solver search log')
    parser.add_argument('--four', action='store_true', dest='size4',
                        default=False,
                        help='whether or not to use 4 demand nodes in problem.  Defaults to false, which will use 5 nodes')
    parser.add_argument('--seven', action='store_true', dest='size7',
                        default=False,
                        help='whether or not to use 7 demand nodes in problem.  Defaults to false, which will use 5 nodes')
    parser.add_argument('--cumulative_constraint', action='store_true', dest='cumulative_constraint',
                        default=False,
                        help='whether or not to use constraints on accumulated time to prevent single unit and combo truck from being used simultaneously')
    parser.add_argument('--fake_nodes', action='store_true', dest='fake_nodes',
                        default=False,
                        help='whether or not to use vehicle-specific fake nodes to prevent single unit and combo truck from being used simultaneously')
    parser.add_argument('--fake_nodes_constraints', action='store_true', dest='fake_nodes_constraints',
                        default=False,
                        help='whether or not to use vehicle-specific fake nodes to prevent single unit and combo truck from being used simultaneously')
    parser.add_argument('-v,--vehicles', type=int, dest='vehicles', default=2,
                        help='number of vehicles to use, each optionally being either a single unit (just the truck) or a combo unit (truck + trailer)')
    parser.add_argument('--combo_cost', type=int, dest='combo_cost', default=5,
                        help='link cost multiplier for using a combo vehicle (truck + trailer)')
    parser.add_argument('--combo_capacity', type=int, dest='combo_capacity', default=3,
                        help='total capacity of a combo vehicle (truck + trailer)')
    parser.add_argument('--single_cost', type=int, dest='single_cost', default=1,
                        help='link cost multiplier for using a single vehicle (truck only)')
    parser.add_argument('--single_capacity', type=int, dest='single_capacity', default=1,
                        help='total capacity of a single vehicle (truck only)')
    parser.add_argument('-t,--timelimit', type=int, dest='timelimit', default=60,
                        help='solver time limit, in seconds; default 60 (one minute)')
    parser.add_argument('--guided_local', action='store_true', dest='guided_local',
                        default=False,
                        help='whether or not to use the guided local search metaheuristic')
    args = parser.parse_args()


    """Solve the CVRP problem."""
    # Instantiate the data problem.
    data = create_data_model(args)
    num_veh = len(data['vehicle_costs'])
    # assert num_veh == 2 * args.vehicles
    # assert num_veh == len(data['vehicle_capacities'])

    if args.fake_nodes:
        for veh_pair in range(0, num_veh//2):
            newnode_1 = vehicle_dummy_nodes(data)
            newnode_2 = vehicle_dummy_nodes(data)
        print(data['distance_matrix'])

    num_nodes = len(data['distance_matrix'])
    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(
        num_nodes, num_veh, data['depot'])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)
    solver = routing.solver()

    transit_callback_index = routing.RegisterTransitCallback(partial(distance_callback,
                                                                     data,
                                                                     manager))

    # use per-vehicle arc cost evaluators

    vehicle_transits = [
        routing.RegisterTransitCallback(
            partial(vehicle_distance_callback, data, v, manager)
        ) for v in range(0,num_veh)]

    vehicle_costs = [
        routing.SetArcCostEvaluatorOfVehicle(
            t,v
        ) for (t,v) in zip(vehicle_transits,
                           range(0,num_veh))]

    # create travel cost dimension dependent on vehicle type
    routing.AddDimensionWithVehicleTransits(
        vehicle_transits,
        0,      # no slack
        300000, # some really large time
        True,
        "Cost")
    cost_dimension = routing.GetDimensionOrDie("Cost")

    # Add Capacity constraint.
    demand_callback_index = routing.RegisterUnaryTransitCallback(
        partial(demand_callback, data, manager))
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        data['vehicle_capacities'],  # vehicle maximum capacities
        True,  # start cumul to zero
        'Capacity')


    # count
    count_dimension_name = 'count'
    routing.AddConstantDimension(
        1, # increment by one every time
        num_nodes,  # max count is visit all the nodes
        True,  # set count to zero
        count_dimension_name)
    count_dimension = routing.GetDimensionOrDie(count_dimension_name)

    # set constraints such that truck, truck and trailer cannot both be used
    for veh_pair in range(0, num_veh//2):
        # buggy dead reckoning, but truck-trailer is first, truck single unit second
        combo = veh_pair*2
        single = veh_pair*2 + 1
        if args.cumulative_constraint:
            index_combo = routing.End(combo)
            index_single = routing.End(single)

            end_time_combo = cost_dimension.CumulVar(index_combo)
            end_time_single = cost_dimension.CumulVar(index_single)

            combo_on = end_time_combo > 0
            single_on = end_time_single > 0

            # constrain solver to prevent both being on
            # truth table
            #
            # combo_on     single_on   multiply  descr
            #   0             0           0      both unused; okay
            #   1             0           0      combo on only; okay
            #   0             1           0      single on only; okay
            #   1             1           1      both on; prevent
            #
            solver.Add(combo_on * single_on == 0)
        if args.fake_nodes_constraints:
            newnode_1 = manager.NodeToIndex(len(data['demands']) + 2*veh_pair)
            newnode_2 = manager.NodeToIndex(len(data['demands']) + 2*veh_pair + 1)

            node1_on = routing.VehicleVar(newnode_1) > -1
            node1_combo = routing.VehicleVar(newnode_1) == combo
            node2_on = routing.VehicleVar(newnode_2) > -1
            node2_single = routing.VehicleVar(newnode_2) == single
            conditional_1 = solver.ConditionalExpression(
                node1_on, node1_combo, 1)
            conditional_2 = solver.ConditionalExpression(
                node2_on, node2_single, 1)

            solver.Add(conditional_1>=1)
            solver.Add(conditional_2>=1)
            # routing.AddDisjunction([newnode_1, newnode_2], -1, 1)

            # Force dummy nodes to go first
            count_dimension.SetCumulVarSoftUpperBound(newnode_1,
                                                      1,
                                                      1000000)
            count_dimension.SetCumulVarSoftUpperBound(newnode_2,
                                                      1,
                                                      1000000)

            #Force minimal usage?
            index_combo = routing.End(combo)
            index_single = routing.End(single)
            combo_used = count_dimension.CumulVar(index_combo) > 2
            single_used = count_dimension.CumulVar(index_single) > 2

            solver.Add(combo_used * single_used == 0)




    # optional disjunctions, depending on command line args
    if args.single_disjunctions:
        print('single node disjunction penalty is',args.singlepenalty)
        disjunctions = [routing.AddDisjunction([manager.NodeToIndex(i)],args.singlepenalty)
                        for i in range(1,len(data['demands']))]
        print('added',len(disjunctions),'disjunctions, one per node')
    # Setting parameters and first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.time_limit.seconds =  args.timelimit  # timelimit
    search_parameters.local_search_operators.use_path_lns = pywrapcp.BOOL_TRUE
    search_parameters.local_search_operators.use_inactive_lns = pywrapcp.BOOL_TRUE
    search_parameters.lns_time_limit.seconds = 10000  # 10000 milliseconds
    search_parameters.first_solution_strategy = (
        # routing_enums_pb2.FirstSolutionStrategy.LOCAL_CHEAPEST_ARC)  # works
        routing_enums_pb2.FirstSolutionStrategy.GLOBAL_CHEAPEST_ARC) # works
        # routing_enums_pb2.FirstSolutionStrategy.SAVINGS)    # works
        # routing_enums_pb2.FirstSolutionStrategy.FIRST_UNBOUND_MIN_VALUE)    # crazy suboptimal
        # routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC)    # suboptimal
        # routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)   # suboptimal
        # routing_enums_pb2.FirstSolutionStrategy.PATH_MOST_CONSTRAINED_ARC) # suboptimal
        # routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION) # no assignment
        # routing_enums_pb2.FirstSolutionStrategy.LOCAL_CHEAPEST_INSERTION)    # no assignment
        # routing_enums_pb2.FirstSolutionStrategy.ALL_UNPERFORMED) # no assignment
        # routing_enums_pb2.FirstSolutionStrategy.BEST_INSERTION)    # no assignment
        # routing_enums_pb2.FirstSolutionStrategy.CHRISTOFIDES)    # no assginment
        # routing_enums_pb2.FirstSolutionStrategy.SWEEP)    # no assignment
        # routing_enums_pb2.FirstSolutionStrategy.SEQUENTIAL_CHEAPEST_INSERTION) # no assignment
    if args.guided_local:
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)

    if args.log_search:
        search_parameters.log_search = pywrapcp.BOOL_TRUE

    # Solve the problem.
    assignment = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if assignment:
        print('The Objective Value is {0}'.format(assignment.ObjectiveValue()))
        # examine the xor constraint stuff

        for veh_pair in range(0, num_veh//2):
            # buggy dead reckoning, but truck-trailer is first, truck single unit second
            combo = veh_pair*2
            single = veh_pair*2 + 1
            index_combo = routing.End(combo)
            index_single = routing.End(single)

            end_time_combo_var = cost_dimension.CumulVar(index_combo)
            end_time_single_var = cost_dimension.CumulVar(index_single)

            end_time_combo = assignment.Value(end_time_combo_var)
            end_time_single = assignment.Value(end_time_single_var)
            print('Truck',veh_pair,
                  'travel time\n     combo:',end_time_combo,
                  '\n     single:',end_time_single)
        print_solution(data, manager, routing, assignment)
    else:
        print('no assignment')

if __name__ == '__main__':
    main()
