// Copyright 2010-2018 Google LLC
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// [START program]
// [START import]
#include <vector>
#include <getopt.h>
#include <stdio.h>     /* for printf */
#include "ortools/constraint_solver/routing.h"
#include "ortools/constraint_solver/routing_enums.pb.h"
#include "ortools/constraint_solver/routing_index_manager.h"
#include "ortools/constraint_solver/routing_parameters.h"
// [END import]

/* Flag set by ‘--logging’. */
static int logging_flag;

/* Flag set by ‘--disjunctions’. */
static int disjunctions_flag;

/* Flag set by ‘--cumulative_constraint’. */
static int constraint_flag;

/* Flag set by ‘--fake_nodes’. */
static int fake_nodes_flag;

/* Flag set by ‘--fake_constraints’. */
static int fake_constraints_flag;

struct modelparams
{
  int singlepenalty;
  int vehicles;
  int64 single_cost;
  int64 combo_cost;
  int64 single_capacity;
  int64 combo_capacity;
  int timelimit;
  modelparams() :
    singlepenalty(1), vehicles(2), single_cost(1), single_capacity(1), combo_cost(10), combo_capacity(5), timelimit(10) {}

};


namespace operations_research {
  // [START data_model]
  struct DataModel {
    const std::vector<std::vector<int64>> distance_matrix{
                                                          {0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3},
                                                          {3, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
                                                          {3, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
                                                          {3, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
                                                          {3, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
                                                          {3, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
                                                          {3, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
                                                          {3, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1},
                                                          {3, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1},
                                                          {3, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1},
                                                          {3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1},
                                                          {3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1},
                                                          {3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1},
                                                          {3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1},
                                                          {3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1},
                                                          {3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1},
                                                          {3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0},
    };
    // [START demands]
    const std::vector<int64> demands{
                                     0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    };
    // [END demands]
    // [START capacities_costs]
    std::vector<int64> vehicle_capacities; //{5, 2, 5, 2, 5, 1, 5, 1};
    std::vector<int64> vehicle_costs;      //{60, 20, 60, 20, 50, 10, 50, 1};
    // [END capacities_costs]
    int num_vehicles = 0;

    const RoutingIndexManager::NodeIndex depot{0};

    DataModel( modelparams *params){
      for (int vehicle_pair = 0; vehicle_pair < params->vehicles/2; ++vehicle_pair) {

        vehicle_capacities.push_back(params->combo_capacity);
        vehicle_capacities.push_back(params->single_capacity);

        vehicle_costs.push_back(params->combo_cost);
        vehicle_costs.push_back(params->single_cost);

        num_vehicles = vehicle_capacities.size();
      }
    };
  };
  // [END data_model]

  // [START solution_printer]
  //! @brief Print the solution.
  //! @param[in] data Data of the problem.
  //! @param[in] manager Index manager used.
  //! @param[in] routing Routing solver used.
  //! @param[in] solution Solution found by the solver.
  void PrintSolution(const DataModel& data, const RoutingIndexManager& manager,
                     const RoutingModel& routing, const Assignment& solution) {
    // Display dropped nodes.
    std::ostringstream dropped_nodes;
    for (int64 node = 0; node < routing.Size(); ++node) {
      if (routing.IsStart(node) || routing.IsEnd(node)) continue;
      if (solution.Value(routing.NextVar(node)) == node) {
        dropped_nodes << " " << manager.IndexToNode(node).value();
      }
    }
    LOG(INFO) << "Dropped nodes:" << dropped_nodes.str();
    LOG(INFO) << "Objective value:" << solution.ObjectiveValue();
    // Display routes
    int64 total_distance{0};
    int64 total_load{0};
    for (int vehicle_id = 0; vehicle_id < data.num_vehicles; ++vehicle_id) {
      int64 index = routing.Start(vehicle_id);
      LOG(INFO) << "Route for Vehicle " << vehicle_id << ":";
      int64 route_distance{0};
      int64 route_load{0};
      std::ostringstream route;
      while (routing.IsEnd(index) == false) {
        int64 node_index = manager.IndexToNode(index).value();
        route_load += data.demands[node_index];
        route << node_index << " Load(" << route_load << ") -> ";
        int64 previous_index = index;
        index = solution.Value(routing.NextVar(index));
        route_distance += const_cast<RoutingModel&>(routing).GetArcCostForVehicle(
                                                                                  previous_index, index, int64{vehicle_id});
      }
      LOG(INFO) << route.str() << manager.IndexToNode(index).value();
      LOG(INFO) << "Distance of the route: " << route_distance << "m";
      LOG(INFO) << "Load of the route: " << route_load;
      total_distance += route_distance;
      total_load += route_load;
    }
    LOG(INFO) << "Total distance of all routes: " << total_distance << "m";
    LOG(INFO) << "Total load of all routes: " << total_load;
    LOG(INFO) << "";
    LOG(INFO) << "Advanced usage:";
    LOG(INFO) << "Problem solved in " << routing.solver()->wall_time() << "ms";
  }
  // [END solution_printer]

  void VrpDropNodes( modelparams *params) {
    // Instantiate the data problem.
    // [START data]
    DataModel data(params);
    // [END data]

    // Create Routing Index Manager
    // [START index_manager]
    RoutingIndexManager manager(data.distance_matrix.size(), data.num_vehicles,
                                data.depot);
    // [END index_manager]

    // Create Routing Model.
    // [START routing_model]
    RoutingModel routing(manager);
    // [END routing_model]

    // Create and register a transit callback.
    // [START transit_callback]
    const int transit_callback_index =
      routing.RegisterTransitCallback(
                                      [&data, &manager](int64 from_index, int64 to_index) -> int64 {
                                        // Convert from routing variable Index to distance matrix NodeIndex.
                                        auto from_node = manager.IndexToNode(from_index).value();
                                        auto to_node = manager.IndexToNode(to_index).value();
                                        return data.distance_matrix[from_node][to_node];
                                      });
    // [END transit_callback]

    // Define cost of each arc.
    // [START arc_cost]
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index);
    // [END arc_cost]

    // Define cost of each vehicle.
    // [START vehicle_cost]
    for (int vehicle_id = 0; vehicle_id < data.num_vehicles; ++vehicle_id) {
      routing.SetFixedCostOfVehicle(data.vehicle_costs[vehicle_id], vehicle_id);
    }
    // [END arc_cost]

    // Add Capacity constraint.
    // [START capacity_constraint]
    const int demand_callback_index = routing.RegisterUnaryTransitCallback(
                                                                           [&data, &manager](int64 from_index) -> int64 {
                                                                             // Convert from routing variable Index to demand NodeIndex.
                                                                             auto from_node = manager.IndexToNode(from_index).value();
                                                                             return data.demands[from_node];
                                                                           });
    routing.AddDimensionWithVehicleCapacity(
                                            demand_callback_index,    // transit callback index
                                            int64{0},                 // null capacity slack
                                            data.vehicle_capacities,  // vehicle maximum capacities
                                            true,                     // start cumul to zero
                                            "Capacity");

    // Add Time constraint.
    // [START time_constraint]
    std::string time{"Time"};
    routing.AddDimension(transit_callback_index,  // transit callback index
                         int64{0},               // no slack
                         int64{3000000},               // big number for horizon
                         true,  // force start time cumul to zero
                         time);
    const RoutingDimension& time_dimension = routing.GetDimensionOrDie(time);

    // Allow to drop nodes.
    int64 penalty{100000};
    for (int i = 1; i < data.distance_matrix.size(); ++i) {
      routing.AddDisjunction(
                             {manager.NodeToIndex(RoutingIndexManager::NodeIndex(i))}, penalty);
    }
    // [END capacity_constraint]
    auto solver = routing.solver();
    // Add constraint that truck or truck with trailer, but not both
    for (int vehicle_pair = 0; vehicle_pair < data.num_vehicles/2; ++vehicle_pair) {
      int combo_id = vehicle_pair * 2;
      int single_id = vehicle_pair * 2 + 1;
      int64 index_combo = routing.End(combo_id);
      int64 index_single = routing.End(single_id);
      auto end_time_combo = time_dimension.CumulVar(index_combo);
      auto end_time_single = time_dimension.CumulVar(index_single);
      auto combo_on = solver->MakeIsGreaterCstVar(end_time_combo, 0);
      auto single_on = solver->MakeIsGreaterCstVar(end_time_single, 0);
      solver->AddConstraint(solver->MakeEquality(solver->MakeProd(combo_on,single_on),0));
    }


    // Setting first solution heuristic.
    // [START parameters]
    RoutingSearchParameters searchParameters = DefaultRoutingSearchParameters();
    searchParameters.set_first_solution_strategy(
                                                 //FirstSolutionStrategy::LOCAL_CHEAPEST_ARC);
                                                 FirstSolutionStrategy::GLOBAL_CHEAPEST_ARC);
    //FirstSolutionStrategy::ALL_UNPERFORMED);
    searchParameters.set_local_search_metaheuristic(
                                                    LocalSearchMetaheuristic::GUIDED_LOCAL_SEARCH);
    //searchParameters.set_log_search(true);
    searchParameters.mutable_time_limit()->set_seconds(10);
    // [END parameters]

    // Solve the problem.
    // [START solve]
    const Assignment* solution = routing.SolveWithParameters(searchParameters);
    // [END solve]

    // Print solution on console.
    // [START print_solution]
    PrintSolution(data, manager, routing, *solution);
    // [END print_solution]
  }
}  // namespace operations_research



int main(int argc, char** argv) {

  int c;
  modelparams *param = new modelparams();

  while (1){
    static struct option long_options[] =
      {
       /* These options set a flag. */
       {"logging", no_argument,            &logging_flag, 1},
       {"disjunctions",   no_argument,     &disjunctions_flag, 1},
       {"constraint",   no_argument,       &constraint_flag, 1},
       {"fake_nodes",   no_argument,       &fake_nodes_flag, 1},
       {"fake_nodes_constraint", no_argument, &fake_constraints_flag, 1},
       /* These options don’t set a flag.
          We distinguish them by their indices. */
       {"node_disjunction_penalty",  required_argument, 0, 'n'},
       {"timelimit",  required_argument, 0, 't'},
       {"single_cost",  required_argument, 0, 'r'},
       {"single_capacity",  required_argument, 0, 's'},
       {"combo_cost",  required_argument, 0, 'x'},
       {"combo_capacity",  required_argument, 0, 'y'},
       {"vehicles",  required_argument, 0, 'v'},
       {0, 0, 0, 0}
      };
    /* getopt_long stores the option index here. */
    int option_index = 0;
    c = getopt_long (argc, argv, "a:b:c:d:e:f:v:",
                     long_options, &option_index);

    /* Detect the end of the options. */
    if (c == -1)
      break;

    switch (c)
      {
      case 0:
        /* If this option set a flag, do nothing else now. */
        printf ("case 0, option %s", long_options[option_index].name);
        printf ("\n");
        break;

      case 1:
        /* If this option set a flag, do nothing else now. */
        printf ("case 1, option %s", long_options[option_index].name);
        printf ("\n");
        break;

      case 'n':
        param->singlepenalty = atoi(optarg);
        break;

      case 't':
        param->timelimit = atoi(optarg);
        break;

      case 'r':
        param->single_cost = atoi(optarg);
        break;

      case 's':
        param->single_capacity = atoi(optarg);
        break;

      case 'x':
        param->combo_cost = atoi(optarg);
        break;

      case 'y':
        param->combo_capacity = atoi(optarg);
        break;

      case 'v':
        param->vehicles = atoi(optarg);
        break;

      default:
        printf("?? getopt returned character code 0%o ??\n", c);
        if (atoi(optarg))
          printf (" with arg %s", optarg);
        printf ("\n");
        abort();

      }
  }
  operations_research::VrpDropNodes(param);
  return EXIT_SUCCESS;
}
// [END program]
