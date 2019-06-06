#!/usr/bin/env python3
from six.moves import xrange
from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2
from functools import partial
import argparse


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
            [0, 3, 3, 3, 3, 3, 3, 3],
            [3, 0, 1, 1, 1, 1, 1, 1],
            [3, 1, 0, 1, 1, 1, 1, 1],
            [3, 1, 1, 0, 1, 1, 1, 1],
            [3, 1, 1, 1, 0, 1, 1, 1],
            [3, 1, 1, 1, 1, 0, 1, 1],
            [3, 1, 1, 1, 1, 1, 0, 1],
            [3, 1, 1, 1, 1, 1, 1, 0]
        ]
        data['demands'] = [0, 1, 1, 1, 1, 1, 1, 1 ]

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

    data['vehicle_capacities'] = [3, 1, 3, 1]
    data['depot'] = 0
    data['vehicle_costs'] = [5, 1, 5, 1]
    #data['vehicle_costs'] = [5, 5, 5, 5]
    return data


def print_solution(data, manager, routing, assignment):
    """Prints assignment on console."""
    total_distance = 0
    total_load = 0
    for vehicle_id in range(0,len(data['vehicle_costs'])):
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        route_distance = 0
        route_load = 0
        arc_cost = 0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_load += data['demands'][node_index]
            plan_output += ' {0} Load({1}) Cost({2}) -> '.format(node_index, route_load, arc_cost)
            previous_index = index
            index = assignment.Value(routing.NextVar(index))
            arc_cost = routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
            route_distance += arc_cost
        plan_output += ' {0} Load({1}) Cost({2})\n'.format(
            manager.IndexToNode(index), route_load, arc_cost)
        plan_output += 'Distance of the route: {}m\n'.format(route_distance)
        plan_output += 'Load of the route: {}\n'.format(route_load)
        print(plan_output)
        total_distance += route_distance
        total_load += route_load
    print('Total distance of all routes: {}m'.format(total_distance))
    print('Total load of all routes: {}'.format(total_load))


def main():
    parser = argparse.ArgumentParser(description='Play around with various options relating to disjunctions')
    parser.add_argument('--cardinality_disjunction', type=bool, dest='multi_disjunctions',
                        default=False,
                        help='whether or not to use the max cardinality disjunction')
    parser.add_argument('-p,--penalty', type=int, dest='penalty', default=0,
                        help='penalty value to use for cardinality disjunction')
    parser.add_argument('-c,--cardinality', type=int, dest='cardinality', default=2,
                        help='max cardinality to use')
    parser.add_argument('-d,--disjunctions', type=bool, dest='single_disjunctions',
                        default=False,
                        help='whether or not to use the single-node disjunctions')
    parser.add_argument('--singlepenalty', type=int, dest='singlepenalty', default=1,
                        help='penalty value to use for single element disjunction')
    parser.add_argument('-l,--log_search', type=bool, dest='log_search',
                        default=False,
                        help='whether or not to output the solver search log')
    parser.add_argument('--four', type=bool, dest='size4',
                        default=False,
                        help='whether or not to use 4 demand nodes in problem.  Defaults to false, which will use 5 nodes')
    parser.add_argument('--seven', type=bool, dest='size7',
                        default=False,
                        help='whether or not to use 7 demand nodes in problem.  Defaults to false, which will use 5 nodes')
    args = parser.parse_args()


    """Solve the CVRP problem."""
    # Instantiate the data problem.
    data = create_data_model(args)
    num_nodes = len(data['demands'])
    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(
        num_nodes, len(data['vehicle_costs']), data['depot'])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)
    solver = routing.solver()

    # Create and register a transit callback.
    def distance_callback(manager, from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    def vehicle_distance_callback(vehicle, manager, from_index, to_index):
        """Returns the distance between the two nodes for a vehicle."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]*data['vehicle_costs'][vehicle]

    transit_callback_index = routing.RegisterTransitCallback(partial(distance_callback,
                                                                     manager))

    # use per-vehicle arc cost evaluators
    vehicle_transits = [
        routing.SetArcCostEvaluatorOfVehicle(
            routing.RegisterTransitCallback(
                partial(vehicle_distance_callback,v,manager)
            ), v
        ) for v in range(0,len(data['vehicle_capacities']))]



    # Add Capacity constraint.
    def demand_callback(from_index):
        """Returns the demand of the node."""
        # Convert from routing variable Index to demands NodeIndex.
        from_node = manager.IndexToNode(from_index)
        return data['demands'][from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(
        demand_callback)
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

    indexA1 = routing.End(0);
    indexA2 = routing.End(1);
    indexA3 = routing.End(2);
    indexA4 = routing.End(3);
    end_count_A1 = count_dimension.CumulVar(indexA1);
    end_count_A2 = count_dimension.CumulVar(indexA2);
    end_count_A3 = count_dimension.CumulVar(indexA3);
    end_count_A4 = count_dimension.CumulVar(indexA4);

    A1_on = end_count_A1 > 1;
    A2_on = end_count_A2 > 1;
    A3_on = end_count_A3 > 1;
    A4_on = end_count_A4 > 1;
    solver.Add(A1_on + A2_on <= 1);
    solver.Add(A3_on + A4_on <= 1);


    # disjunctions on nodes
    # truck cost < Penalty < truck with trailer cost
    if args.multi_disjunctions:
        # penalty = 6+data['vehicle_costs'][0] + 2
        penalty = 10 * data['vehicle_costs'][0] + 1
        if args.penalty>0:
            penalty=args.penalty
        print('disjunction penalty is',penalty)

        pickup_nodes = [manager.NodeToIndex(i)
                            for i in range(1,len(data['demands']))]
        routing.AddDisjunction(pickup_nodes,penalty,args.cardinality)

    if args.single_disjunctions:
        disjunctions = [routing.AddDisjunction([i],args.singlepenalty)
                        for i in range(1,num_nodes)]
    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.local_search_operators.use_path_lns = pywrapcp.BOOL_TRUE
    search_parameters.local_search_operators.use_inactive_lns = pywrapcp.BOOL_TRUE
    search_parameters.lns_time_limit.seconds = 10000  # 10000 milliseconds
    search_parameters.first_solution_strategy = (
    #    routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION)
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    #    routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    if args.log_search:
        search_parameters.log_search = pywrapcp.BOOL_TRUE

    # Solve the problem.
    assignment = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if assignment:
        print('The Objective Value is {0}'.format(assignment.ObjectiveValue()))
        # examine the xor constraint stuff
        print('A1 end count',assignment.Value(end_count_A1))
        print('A2 end count',assignment.Value(end_count_A2))
        print('A3 end count',assignment.Value(end_count_A3))
        print('A4 end count',assignment.Value(end_count_A4))

        print_solution(data, manager, routing, assignment)


if __name__ == '__main__':
    main()
