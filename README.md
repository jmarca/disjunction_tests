# Bugs in disjunctions

This repo examines bugs in disjunctions.

The basic idea is that there are two variations of a single vehicle.
Variation 1 is the vehicle by itself, and variation 2 is the vehicle
with a trailer, which adds capacity but also brings an additional link
travel cost.


# Bug report

The problem is that when one adds disjunctions to all nodes, the
solver decides that it can skip them all.  This is bad for solutions.

The problem is exposed by running the python program
disjunction_fail.py.  If you pass `-h` you can see all the options.

```python
 python disjunction_fail.py  -h
usage: disjunction_fail.py [-h] [-d,--disjunctions]
                           [--singlepenalty SINGLEPENALTY] [-l,--log_search]
                           [--four] [--seven] [--cumulative_constraint]
                           [--fake_nodes] [-v,--vehicles VEHICLES]
                           [--combo_cost COMBO_COST]
                           [--combo_capacity COMBO_CAPACITY]
                           [--single_cost SINGLE_COST]
                           [--single_capacity SINGLE_CAPACITY]

Play around with various options relating to disjunctions

optional arguments:
  -h, --help            show this help message and exit
  -d,--disjunctions     whether or not to use the single-node disjunctions
  --singlepenalty SINGLEPENALTY
                        penalty value to use for single element disjunction
  -l,--log_search       whether or not to output the solver search log
  --four                whether or not to use 4 demand nodes in problem.
                        Defaults to false, which will use 5 nodes
  --seven               whether or not to use 7 demand nodes in problem.
                        Defaults to false, which will use 5 nodes
  --cumulative_constraint
                        whether or not to use constraints on accumulated time
                        to prevent single unit and combo truck from being used
                        simultaneously
  --fake_nodes          whether or not to use vehicle-specific fake nodes to
                        prevent single unit and combo truck from being used
                        simultaneously
  -v,--vehicles VEHICLES
                        number of vehicles to use, each optionally being
                        either a single unit (just the truck) or a combo unit
                        (truck + trailer)
  --combo_cost COMBO_COST
                        link cost multiplier for using a combo vehicle (truck
                        + trailer)
  --combo_capacity COMBO_CAPACITY
                        total capacity of a combo vehicle (truck + trailer)
  --single_cost SINGLE_COST
                        link cost multiplier for using a single vehicle (truck
                        only)
  --single_capacity SINGLE_CAPACITY
                        total capacity of a single vehicle (truck only)
```

Run without any options, the program will generate a simple five node
problem, plus a depot.  The best solution is to choose the truck plus
trailer for both vehicles, and to visit three of the five nodes with
one, and two of the five nodes with the other.  This is demonstrated
below.


```
python disjunction_fail.py    -l 1
WARNING: Logging before InitGoogleLogging() is written to STDERR
I0611 19:59:20.584077     8 search.cc:252] Start search (memory used = 42.73 MB)
I0611 19:59:20.584228     8 search.cc:252] Root node processed (time = 0 ms, constraints = 110, memory used = 42.73 MB)
I0611 19:59:20.584597     8 search.cc:252] Solution #0 (75, time = 0 ms, branches = 52, failures = 8, depth = 33, memory used = 42.73 MB)
I0611 19:59:20.611366     8 search.cc:252] Finished search tree (time = 27 ms, branches = 2599, failures = 1518, neighbors = 338, filtered neighbors = 133, accepted neigbors = 0, memory used = 42.73 MB)
I0611 19:59:20.611438     8 search.cc:252] End search (time = 27 ms, branches = 2599, failures = 1518, memory used = 42.73 MB, speed = 96259 branches/s)
The Objective Value is 75
Truck 0 travel time
     combo: 40
     single: 0
Truck 1 travel time
     combo: 35
     single: 0
Route for vehicle 0:
 0 Load(0) Cost(0) Count(0)->  5 Load(1) Cost(15) Count(1)->  1 Load(2) Cost(5) Count(2)->  4 Load(3) Cost(5) Count(3)->  0 Load(3) Cost(15) Count(4)
Distance of the route: 40m
Load of the route: 3

Route for vehicle 1:
 0 Load(0) Cost(0) Count(0)->  0 Load(0) Cost(0) Count(1)
Distance of the route: 0m
Load of the route: 0

Route for vehicle 2:
 0 Load(0) Cost(0) Count(0)->  2 Load(1) Cost(15) Count(1)->  3 Load(2) Cost(5) Count(2)->  0 Load(2) Cost(15) Count(3)
Distance of the route: 35m
Load of the route: 2

Route for vehicle 3:
 0 Load(0) Cost(0) Count(0)->  0 Load(0) Cost(0) Count(1)
Distance of the route: 0m
Load of the route: 0

Total distance of all routes: 75m
Total load of all routes: 5
```

Although this run looks good, it doesn't really prove that the solver
is in fact doing the right thing in choosing the two different
vehicles.  This is just a lucky combination of the random number
generators in the universe creating a false positive.

To show this, you can increase the cost of using a combo truck, so
that the solver prefers using single unit trucks.

```
python disjunction_fail.py  --combo_cost 10
The Objective Value is 92
Truck 0 travel time
     combo: 0
     single: 6
Truck 1 travel time
     combo: 80
     single: 6
Route for vehicle 0:
 0 Load(0) Cost(0) Count(0)->  0 Load(0) Cost(0) Count(1)
Distance of the route: 0m
Load of the route: 0

Route for vehicle 1:
 0 Load(0) Cost(0) Count(0)->  5 Load(1) Cost(3) Count(1)->  0 Load(1) Cost(3) Count(2)
Distance of the route: 6m
Load of the route: 1

Route for vehicle 2:
 0 Load(0) Cost(0) Count(0)->  4 Load(1) Cost(30) Count(1)->  2 Load(2) Cost(10) Count(2)->  3 Load(3) Cost(10) Count(3)->  0 Load(3) Cost(30) Count(4)
Distance of the route: 80m
Load of the route: 3

Route for vehicle 3:
 0 Load(0) Cost(0) Count(0)->  1 Load(1) Cost(3) Count(1)->  0 Load(1) Cost(3) Count(2)
Distance of the route: 6m
Load of the route: 1

Total distance of all routes: 92m
Total load of all routes: 5
```

So you see, the solver here is choosing to use as many of the cheap
single unit trucks as possible, so it uses both types of vehicle two.
This is wrong.

To fix this, flip on the option to use the `--cumulative_constraint`.
This will activate code that looks like:

```python
index_combo = routing.End(combo)
index_single = routing.End(single)
end_time_combo = time_dimension.CumulVar(index_combo)
end_time_single = time_dimension.CumulVar(index_single)
combo_on = end_time_combo > 0
single_on = end_time_single > 0
solver.Add(combo_on * single_on == 0)
```

This gets back to the earlier solution, but this time we know that the
solver is not accidentally stumbling upon it.  Rather it is being
forced to choose it based on the constraint that only one of the two
flavors of each vehicle can be used.

```
python disjunction_fail.py  --combo_cost 10 --cumulative_constraint
The Objective Value is 150
Truck 0 travel time
     combo: 80
     single: 0
Truck 1 travel time
     combo: 70
     single: 0
Route for vehicle 0:
 0 Load(0) Cost(0) Count(0)->  5 Load(1) Cost(30) Count(1)->  1 Load(2) Cost(10) Count(2)->  4 Load(3) Cost(10) Count(3)->  0 Load(3) Cost(30) Count(4)
Distance of the route: 80m
Load of the route: 3

Route for vehicle 1:
 0 Load(0) Cost(0) Count(0)->  0 Load(0) Cost(0) Count(1)
Distance of the route: 0m
Load of the route: 0

Route for vehicle 2:
 0 Load(0) Cost(0) Count(0)->  2 Load(1) Cost(30) Count(1)->  3 Load(2) Cost(10) Count(2)->  0 Load(2) Cost(30) Count(3)
Distance of the route: 70m
Load of the route: 2

Route for vehicle 3:
 0 Load(0) Cost(0) Count(0)->  0 Load(0) Cost(0) Count(1)
Distance of the route: 0m
Load of the route: 0

Total distance of all routes: 150m
Total load of all routes: 5
```

There are also options `--four`  and `--seven`, that create a
four-node and an eleven-node problem, respectively.  The `--seven`
option demonstrates that the problem cannot be solved without
disjunctions in the general case, because without a disjunction the
solver cannot drop nodes.  While there is a `--vehicles` parameter
that will increase the numbers of vehicles, in general with a small
number of vehicles, the solver should be able to drop nodes and come
up with an assignment.


## Enter the bug with disjunctions

So in theory, all one has to do is add disjunctions, and the solver
will be allowed to drop nodes and the problem should be solved.  This
is where the bug with disjunctions was discovered.

To demonstrate using disjunctions, there are command line flags for
that. The first is the `-d` flag that turns on disjunctions for all
nodes, and then the `--singlepenalty N` argument that takes the value
of the disjunction.

The next run shows using three vehicles with the eleven node case,
with a disjunction penalty of 10.  Three single trucks are used, as
combo units are more expensive than dropping nodes.

```
python disjunction_fail.py  --combo_cost 10 --cumulative_constraint --seven -d --singlepenalty 10
single node disjunction penalty is 10
added 11 disjunctions, one per node
The Objective Value is 102
Truck 0 travel time
     combo: 0
     single: 6
Truck 1 travel time
     combo: 0
     single: 6
Route for vehicle 0:
 0 Load(0) Cost(0) Count(0)->  0 Load(0) Cost(0) Count(1)
Distance of the route: 0m
Load of the route: 0

Route for vehicle 1:
 0 Load(0) Cost(0) Count(0)->  11 Load(1) Cost(3) Count(1)->  0 Load(1) Cost(3) Count(2)
Distance of the route: 6m
Load of the route: 1

Route for vehicle 2:
 0 Load(0) Cost(0) Count(0)->  0 Load(0) Cost(0) Count(1)
Distance of the route: 0m
Load of the route: 0

Route for vehicle 3:
 0 Load(0) Cost(0) Count(0)->  1 Load(1) Cost(3) Count(1)->  0 Load(1) Cost(3) Count(2)
Distance of the route: 6m
Load of the route: 1

Total distance of all routes: 12m
Total load of all routes: 2
```

As the `--singlepenalty` cost goes up, it becomes possible to use
combo trucks.  The cross-over point is at 65, done by trial and error,
not by actually computing where it should be.

```
 python disjunction_fail.py  -v 3 --combo_cost 10 --cumulative_constraint --seven -d --singlepenalty 65 -l
single node disjunction penalty is 65
added 11 disjunctions, one per node
WARNING: Logging before InitGoogleLogging() is written to STDERR
I0613 04:49:36.835664   714 routing.cc:2833] All Unperformed Solution (715, time = 2 ms, memory used = 128.57 MB)
I0613 04:49:36.835750   714 search.cc:252] Start search (memory used = 128.57 MB)
I0613 04:49:36.836256   714 search.cc:252] Root node processed (time = 0 ms, constraints = 241, memory used = 128.57 MB)
I0613 04:49:36.837337   714 search.cc:252] Solution #0 (710, time = 1 ms, branches = 44, failures = 0, depth = 33, memory used = 128.57 MB)
I0613 04:49:36.837924   714 search.cc:252] Solution #1 (656, objective maximum = 710, time = 2 ms, branches = 47, failures = 2, depth = 33, Relocate<1>, neighbors = 1, filtered neighbors = 1, accepted neighbors = 1, memory used = 128.57 MB)
I0613 04:49:36.839738   714 search.cc:252] Solution #2 (651, objective maximum = 710, time = 3 ms, branches = 51, failures = 5, depth = 33, MakeActiveOperator, neighbors = 26, filtered neighbors = 3, accepted neighbors = 2, memory used = 128.57 MB)
I0613 04:49:36.840333   714 search.cc:252] Solution #3 (596, objective maximum = 710, time = 4 ms, branches = 54, failures = 7, depth = 33, MakeActiveOperator, neighbors = 27, filtered neighbors = 4, accepted neighbors = 3, memory used = 128.57 MB)
I0613 04:49:36.840962   714 search.cc:252] Solution #4 (541, objective maximum = 710, time = 5 ms, branches = 59, failures = 9, depth = 33, MakeActiveOperator, neighbors = 28, filtered neighbors = 5, accepted neighbors = 4, memory used = 128.57 MB)
I0613 04:49:36.841809   714 search.cc:252] Solution #5 (536, objective maximum = 710, time = 5 ms, branches = 62, failures = 12, depth = 33, MakeActiveOperator, neighbors = 34, filtered neighbors = 7, accepted neighbors = 5, memory used = 128.57 MB)
I0613 04:49:36.842386   714 search.cc:252] Solution #6 (481, objective maximum = 710, time = 6 ms, branches = 66, failures = 14, depth = 33, MakeActiveOperator, neighbors = 35, filtered neighbors = 8, accepted neighbors = 6, memory used = 128.57 MB)
I0613 04:49:36.843052   714 search.cc:252] Solution #7 (426, objective maximum = 710, time = 7 ms, branches = 69, failures = 16, depth = 33, MakeActiveOperator, neighbors = 36, filtered neighbors = 9, accepted neighbors = 7, memory used = 128.57 MB)
I0613 04:49:37.546200   714 search.cc:252] Finished search tree (time = 710 ms, branches = 42267, failures = 21711, neighbors = 869, filtered neighbors = 397, accepted neigbors = 7, memory used = 128.57 MB)
I0613 04:49:37.546525   714 search.cc:252] End search (time = 710 ms, branches = 42267, failures = 21711, memory used = 128.57 MB, speed = 59530 branches/s)
The Objective Value is 426
Truck 0 travel time
     combo: 0
     single: 6
Truck 1 travel time
     combo: 80
     single: 0
Truck 2 travel time
     combo: 80
     single: 0
Route for vehicle 0:
 0 Load(0) Cost(0) Count(0)->  0 Load(0) Cost(0) Count(1)
Distance of the route: 0m
Load of the route: 0

Route for vehicle 1:
 0 Load(0) Cost(0) Count(0)->  11 Load(1) Cost(3) Count(1)->  0 Load(1) Cost(3) Count(2)
Distance of the route: 6m
Load of the route: 1

Route for vehicle 2:
 0 Load(0) Cost(0) Count(0)->  3 Load(1) Cost(30) Count(1)->  2 Load(2) Cost(10) Count(2)->  1 Load(3) Cost(10) Count(3)->  0 Load(3) Cost(30) Count(4)
Distance of the route: 80m
Load of the route: 3

Route for vehicle 3:
 0 Load(0) Cost(0) Count(0)->  0 Load(0) Cost(0) Count(1)
Distance of the route: 0m
Load of the route: 0

Route for vehicle 4:
 0 Load(0) Cost(0) Count(0)->  6 Load(1) Cost(30) Count(1)->  5 Load(2) Cost(10) Count(2)->  4 Load(3) Cost(10) Count(3)->  0 Load(3) Cost(30) Count(4)
Distance of the route: 80m
Load of the route: 3

Route for vehicle 5:
 0 Load(0) Cost(0) Count(0)->  0 Load(0) Cost(0) Count(1)
Distance of the route: 0m
Load of the route: 0

Total distance of all routes: 166m
Total load of all routes: 7
```

With 4 nodes of the 11 dropped, that is a dropped cost of 265.
Serving three nodes with a combo truck costs 80, but for some reason
that third truck is left using just the single unit, not the combo.
It seems that it would make sense to use the combo unit (at a cost of
80) and save the cost of dropping two nodes (130) for a net savings
of 50.  However, the solver will not do that.  In fact, you can bump
up the disjunction penalty as high as you like and the solver still
won't use that third combo truck.

```
python disjunction_fail.py  -v 3 --combo_cost 10 --cumulative_constraint --seven -d --singlepenalty 1000000000000
single node disjunction penalty is 1000000000000
added 11 disjunctions, one per node
The Objective Value is 4000000000166
Truck 0 travel time
     combo: 0
     single: 6
Truck 1 travel time
     combo: 80
     single: 0
Truck 2 travel time
     combo: 80
     single: 0
...etc, same as before...
```

This is the bug.  The previous output sheds a little light on it, as I
included the log of the solver.  It seems the solver gets the idea
that dropping all the nodes is the worst case, and so it gets stuck
trying to satisfy the disjunctions and somehow doesn't know to flip
the last truck over to using combo units.

If you turn on 4 trucks, in theory it should be able to serve all the
demands, but it can't and won't, as it cannot turn on that last truck:

```
python disjunction_fail.py  -v 4 --combo_cost 10 --cumulative_constraint --seven -d --singlepenalty 1000000000000
single node disjunction penalty is 1000000000000
added 11 disjunctions, one per node
The Objective Value is 1000000000246
Truck 0 travel time
     combo: 0
     single: 6
Truck 1 travel time
     combo: 80
     single: 0
Truck 2 travel time
     combo: 80
     single: 0
Truck 3 travel time
     combo: 80
     single: 0
```

## Hackity hack

So I figured out a solution to this, and I don't really know why it
works.  But it does.

Essentially, I create dummy nodes, two per vehicle, one for each of
the vehicle flavors (combo or single).  These nodes are restricted to
being served by a unique vehicle, but they are not used in a
disjunction of any sort (I tried that first and there was no joy in
Mudville).

First, without the fake nodes, the solver log looks like this:

```
python disjunction_fail.py  -v 4 --combo_cost 10 --cumulative_constraint --seven -d --singlepenalty 1000000000000 -l
single node disjunction penalty is 1000000000000
added 11 disjunctions, one per node
WARNING: Logging before InitGoogleLogging() is written to STDERR
I0613 05:04:42.336885   786 routing.cc:2833] All Unperformed Solution (11000000000000, time = 2 ms, memory used = 128.61 MB)
I0613 05:04:42.336992   786 search.cc:252] Start search (memory used = 128.61 MB)
I0613 05:04:42.337414   786 search.cc:252] Root node processed (time = 0 ms, constraints = 274, memory used = 128.65 MB)
I0613 05:04:42.338402   786 search.cc:252] Solution #0 (10000000000060, time = 1 ms, branches = 44, failures = 0, depth = 33, memory used = 128.65 MB)
I0613 05:04:42.338948   786 search.cc:252] Solution #1 (10000000000006, objective maximum = 10000000000060, time = 1 ms, branches = 47, failures = 2, depth = 33, Relocate<1>, neighbors = 1, filtered neighbors = 1, accepted neighbors = 1, memory used = 128.65 MB)
I0613 05:04:42.341423   786 search.cc:252] Solution #2 (9000000000066, objective maximum = 10000000000060, time = 4 ms, branches = 51, failures = 5, depth = 33, MakeActiveOperator, neighbors = 34, filtered neighbors = 3, accepted neighbors = 2, memory used = 128.65 MB)
I0613 05:04:42.342036   786 search.cc:252] Solution #3 (8000000000076, objective maximum = 10000000000060, time = 4 ms, branches = 54, failures = 7, depth = 33, MakeActiveOperator, neighbors = 35, filtered neighbors = 4, accepted neighbors = 3, memory used = 128.65 MB)
I0613 05:04:42.342770   786 search.cc:252] Solution #4 (7000000000086, objective maximum = 10000000000060, time = 5 ms, branches = 59, failures = 9, depth = 33, MakeActiveOperator, neighbors = 36, filtered neighbors = 5, accepted neighbors = 4, memory used = 128.65 MB)
I0613 05:04:42.343665   786 search.cc:252] Solution #5 (6000000000146, objective maximum = 10000000000060, time = 6 ms, branches = 62, failures = 12, depth = 33, MakeActiveOperator, neighbors = 42, filtered neighbors = 7, accepted neighbors = 5, memory used = 128.65 MB)
I0613 05:04:42.344278   786 search.cc:252] Solution #6 (5000000000156, objective maximum = 10000000000060, time = 7 ms, branches = 66, failures = 14, depth = 33, MakeActiveOperator, neighbors = 43, filtered neighbors = 8, accepted neighbors = 6, memory used = 128.65 MB)
I0613 05:04:42.345014   786 search.cc:252] Solution #7 (4000000000166, objective maximum = 10000000000060, time = 7 ms, branches = 69, failures = 16, depth = 33, MakeActiveOperator, neighbors = 44, filtered neighbors = 9, accepted neighbors = 7, memory used = 128.65 MB)
I0613 05:04:42.346057   786 search.cc:252] Solution #8 (3000000000226, objective maximum = 10000000000060, time = 9 ms, branches = 75, failures = 19, depth = 33, MakeActiveOperator, neighbors = 50, filtered neighbors = 11, accepted neighbors = 8, memory used = 128.65 MB)
I0613 05:04:42.346894   786 search.cc:252] Solution #9 (2000000000236, objective maximum = 10000000000060, time = 9 ms, branches = 78, failures = 21, depth = 33, MakeActiveOperator, neighbors = 51, filtered neighbors = 12, accepted neighbors = 9, memory used = 128.65 MB)
I0613 05:04:42.347501   786 search.cc:252] Solution #10 (1000000000246, objective maximum = 10000000000060, time = 10 ms, branches = 82, failures = 23, depth = 33, MakeActiveOperator, neighbors = 52, filtered neighbors = 13, accepted neighbors = 10, memory used = 128.65 MB)
I0613 05:04:42.787763   786 search.cc:252] Finished search tree (time = 450 ms, branches = 12799, failures = 7483, neighbors = 1566, filtered neighbors = 727, accepted neigbors = 10, memory used = 128.65 MB)
I0613 05:04:42.788107   786 search.cc:252] End search (time = 450 ms, branches = 12799, failures = 7483, memory used = 128.65 MB, speed = 28442 branches/s)
The Objective Value is 1000000000246
```

Then with the fake nodes flag, the solver log looks like this:

```
python disjunction_fail.py  -v 4 --combo_cost 10 --cumulative_constraint --seven -d --singlepenalty 1000000000000 -l --fake_nodes
single node disjunction penalty is 1000000000000
added 11 disjunctions, one per node
WARNING: Logging before InitGoogleLogging() is written to STDERR
I0613 05:05:47.574512   794 search.cc:252] Start search (memory used = 128.61 MB)
I0613 05:05:47.575134   794 search.cc:252] Root node processed (time = 0 ms, constraints = 361, memory used = 128.61 MB)
I0613 05:05:47.577108   794 search.cc:252] Solution #0 (11000000060000, time = 2 ms, branches = 52, failures = 1, depth = 33, memory used = 128.61 MB)
I0613 05:05:47.578279   794 search.cc:252] Solution #1 (11000000050000, objective maximum = 11000000060000, time = 3 ms, branches = 55, failures = 3, depth = 33, Relocate<1>, neighbors = 29, filtered neighbors = 1, accepted neighbors = 1, memory used = 128.61 MB)
I0613 05:05:47.579294   794 search.cc:252] Solution #2 (11000000040000, objective maximum = 11000000060000, time = 4 ms, branches = 59, failures = 5, depth = 33, Relocate<1>, neighbors = 42, filtered neighbors = 2, accepted neighbors = 2, memory used = 128.61 MB)
I0613 05:05:47.580116   794 search.cc:252] Solution #3 (11000000030000, objective maximum = 11000000060000, time = 5 ms, branches = 62, failures = 7, depth = 33, Relocate<1>, neighbors = 53, filtered neighbors = 3, accepted neighbors = 3, memory used = 128.61 MB)
I0613 05:05:47.581044   794 search.cc:252] Solution #4 (11000000020000, objective maximum = 11000000060000, time = 6 ms, branches = 67, failures = 9, depth = 33, Relocate<1>, neighbors = 62, filtered neighbors = 4, accepted neighbors = 4, memory used = 128.61 MB)
I0613 05:05:47.581833   794 search.cc:252] Solution #5 (11000000010000, objective maximum = 11000000060000, time = 7 ms, branches = 70, failures = 11, depth = 33, Relocate<1>, neighbors = 69, filtered neighbors = 5, accepted neighbors = 5, memory used = 128.61 MB)
I0613 05:05:47.582572   794 search.cc:252] Solution #6 (11000000000000, objective maximum = 11000000060000, time = 7 ms, branches = 74, failures = 13, depth = 33, Relocate<1>, neighbors = 74, filtered neighbors = 6, accepted neighbors = 6, memory used = 128.61 MB)
I0613 05:05:47.593364   794 search.cc:252] Solution #7 (10000000100010, objective maximum = 11000000060000, time = 18 ms, branches = 77, failures = 15, depth = 33, MakeActiveOperator, neighbors = 531, filtered neighbors = 7, accepted neighbors = 7, memory used = 128.61 MB)
I0613 05:05:47.594316   794 search.cc:252] Solution #8 (9000000100020, objective maximum = 11000000060000, time = 19 ms, branches = 83, failures = 17, depth = 33, MakeActiveOperator, neighbors = 532, filtered neighbors = 8, accepted neighbors = 8, memory used = 128.61 MB)
I0613 05:05:47.595172   794 search.cc:252] Solution #9 (8000000100030, objective maximum = 11000000060000, time = 20 ms, branches = 86, failures = 19, depth = 33, MakeActiveOperator, neighbors = 533, filtered neighbors = 9, accepted neighbors = 9, memory used = 128.61 MB)
I0613 05:05:47.596709   794 search.cc:252] Solution #10 (7000000200040, objective maximum = 11000000060000, time = 22 ms, branches = 90, failures = 23, depth = 33, MakeActiveOperator, neighbors = 541, filtered neighbors = 12, accepted neighbors = 10, memory used = 128.61 MB)
I0613 05:05:47.597543   794 search.cc:252] Solution #11 (6000000200050, objective maximum = 11000000060000, time = 22 ms, branches = 93, failures = 25, depth = 33, MakeActiveOperator, neighbors = 542, filtered neighbors = 13, accepted neighbors = 11, memory used = 128.61 MB)
I0613 05:05:47.598402   794 search.cc:252] Solution #12 (5000000200060, objective maximum = 11000000060000, time = 23 ms, branches = 98, failures = 27, depth = 33, MakeActiveOperator, neighbors = 543, filtered neighbors = 14, accepted neighbors = 12, memory used = 128.61 MB)
I0613 05:05:47.600446   794 search.cc:252] Solution #13 (4000000300070, objective maximum = 11000000060000, time = 25 ms, branches = 101, failures = 31, depth = 33, MakeActiveOperator, neighbors = 551, filtered neighbors = 17, accepted neighbors = 13, memory used = 128.61 MB)
I0613 05:05:47.601433   794 search.cc:252] Solution #14 (3000000300080, objective maximum = 11000000060000, time = 26 ms, branches = 105, failures = 33, depth = 33, MakeActiveOperator, neighbors = 552, filtered neighbors = 18, accepted neighbors = 14, memory used = 128.61 MB)
I0613 05:05:47.602358   794 search.cc:252] Solution #15 (2000000300090, objective maximum = 11000000060000, time = 27 ms, branches = 108, failures = 35, depth = 33, MakeActiveOperator, neighbors = 553, filtered neighbors = 19, accepted neighbors = 15, memory used = 128.61 MB)
I0613 05:05:47.604465   794 search.cc:252] Solution #16 (1000000400100, objective maximum = 11000000060000, time = 29 ms, branches = 115, failures = 39, depth = 33, MakeActiveOperator, neighbors = 561, filtered neighbors = 22, accepted neighbors = 16, memory used = 128.61 MB)
I0613 05:05:47.605582   794 search.cc:252] Solution #17 (400110, objective maximum = 11000000060000, time = 30 ms, branches = 118, failures = 41, depth = 33, MakeActiveOperator, neighbors = 562, filtered neighbors = 23, accepted neighbors = 17, memory used = 128.61 MB)
I0613 05:05:47.610101   794 search.cc:252] Solution #18 (300160, objective maximum = 11000000060000, time = 35 ms, branches = 189, failures = 79, depth = 33, PathLns, neighbors = 565, filtered neighbors = 26, accepted neighbors = 18, memory used = 128.61 MB)
I0613 05:05:47.981616   794 search.cc:252] Solution #19 (200210, objective maximum = 11000000060000, time = 406 ms, branches = 15346, failures = 8191, depth = 33, PathLns, neighbors = 934, filtered neighbors = 311, accepted neighbors = 19, memory used = 128.64 MB)
I0613 05:05:48.351459   794 search.cc:252] Solution #20 (100260, objective maximum = 11000000060000, time = 776 ms, branches = 29851, failures = 15976, depth = 33, PathLns, neighbors = 1303, filtered neighbors = 596, accepted neighbors = 20, memory used = 128.64 MB)
I0613 05:05:48.678081   794 search.cc:252] Solution #21 (310, objective maximum = 11000000060000, time = 1103 ms, branches = 41527, failures = 22292, depth = 33, PathLns, neighbors = 1644, filtered neighbors = 853, accepted neighbors = 21, memory used = 128.64 MB)
I0613 05:05:49.658802   794 search.cc:252] Finished search tree (time = 2084 ms, branches = 76517, failures = 41328, neighbors = 4625, filtered neighbors = 1736, accepted neigbors = 21, memory used = 128.64 MB)
I0613 05:05:49.659204   794 search.cc:252] End search (time = 2084 ms, branches = 76517, failures = 41328, memory used = 128.64 MB, speed = 36716 branches/s)
The Objective Value is 310
Truck 0 travel time
     combo: 80
     single: 0
Truck 1 travel time
     combo: 80
     single: 0
Truck 2 travel time
     combo: 80
     single: 0
Truck 3 travel time
     combo: 70
     single: 0
```

So what is going on?  I have no idea.  But clearly, there is not "all
unperformed" note in the solver log, so the solver does not think it
can drop all nodes.  It also tries harder to serve nodes.  But other
that those obvious facts, I have no idea why it works better.

The solution is to create dummy nodes that cost nothing and are
totally pointless, and to make sure there are enough for one per
vehicle so the solver can get all the vehicles involved.

I think you can get stupid with the code, but I had higher hopes.

First, to generate dummy nodes, realize that the original five node
distance matrix looks like this:

```python
data['distance_matrix'] = [
    [0, 3, 3, 3, 3, 3],
    [3, 0, 1, 1, 1, 1],
    [3, 1, 0, 1, 1, 1],
    [3, 1, 1, 0, 1, 1],
    [3, 1, 1, 1, 0, 1],
    [3, 1, 1, 1, 1, 0]
]
```

It costs "3" to get to and from the depot to any regular node, and "1"
to get from any node to any other node.  Note that this is the base
cost, what a truck without a trailer would pay.  A combo truck with a
trailer pays more, based on the cost multiplier assigned to that
vehicle.

So given that particular shape of the distance matrix, I created the
following to blow that matrix up with dummy nodes.



```python
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

```

Then to trigger the additional nodes for each vehicle, as simple loop.

```python
if args.fake_nodes:
    for veh_pair in range(0, num_veh//2):
        newnode_1 = vehicle_dummy_nodes(data)
        newnode_2 = vehicle_dummy_nodes(data)
```

And that is it.  Just create those nodes, no additional constraints,
and the solver suddenly keeps all the vehicles in play and therefore
is able to serve all the nodes.

The final assignment of paths to the eleven nodes is as follows:

```
Route for vehicle 0:
 0 Load(0) Cost(0) Count(0)->  19 Load(0) Cost(0) Count(1)->  1 Load(1) Cost(30) Count(2)->  2 Load(2) Cost(10) Count(3)->  3 Load(3) Cost(10) Count(4)->  0 Load(3) Cost(30) Count(5)
Distance of the route: 80m
Load of the route: 3

Route for vehicle 1:
 0 Load(0) Cost(0) Count(0)->  15 Load(0) Cost(0) Count(1)->  0 Load(0) Cost(0) Count(2)
Distance of the route: 0m
Load of the route: 0

Route for vehicle 2:
 0 Load(0) Cost(0) Count(0)->  14 Load(0) Cost(0) Count(1)->  4 Load(1) Cost(30) Count(2)->  5 Load(2) Cost(10) Count(3)->  6 Load(3) Cost(10) Count(4)->  0 Load(3) Cost(30) Count(5)
Distance of the route: 80m
Load of the route: 3

Route for vehicle 3:
 0 Load(0) Cost(0) Count(0)->  16 Load(0) Cost(0) Count(1)->  0 Load(0) Cost(0) Count(2)
Distance of the route: 0m
Load of the route: 0

Route for vehicle 4:
 0 Load(0) Cost(0) Count(0)->  13 Load(0) Cost(0) Count(1)->  7 Load(1) Cost(30) Count(2)->  8 Load(2) Cost(10) Count(3)->  9 Load(3) Cost(10) Count(4)->  0 Load(3) Cost(30) Count(5)
Distance of the route: 80m
Load of the route: 3

Route for vehicle 5:
 0 Load(0) Cost(0) Count(0)->  17 Load(0) Cost(0) Count(1)->  0 Load(0) Cost(0) Count(2)
Distance of the route: 0m
Load of the route: 0

Route for vehicle 6:
 0 Load(0) Cost(0) Count(0)->  12 Load(0) Cost(0) Count(1)->  10 Load(1) Cost(30) Count(2)->  11 Load(2) Cost(10) Count(3)->  0 Load(2) Cost(30) Count(4)
Distance of the route: 70m
Load of the route: 2

Route for vehicle 7:
 0 Load(0) Cost(0) Count(0)->  18 Load(0) Cost(0) Count(1)->  0 Load(0) Cost(0) Count(2)
Distance of the route: 0m
Load of the route: 0

Total distance of all routes: 310m
Total load of all routes: 11
```

## Except for one case

So the `--fake_nodes` thing works, except there is one case where the
solver gets it right without the fake nodes, and the fake nodes gets
it wrong.  For five vehicles, the best solution for the eleven node
case is to have two single trucks, and three combo trucks (`2*1 + 3*3 =
11`).  But with the fake nodes, for some reason the solver wants to run
one single truck, two combo trucks with two pickups each, and two full
trucks (`1 + 2*2 + 2*3 = 11`).

Without fake nodes flag:

```
python disjunction_fail.py  -v 6 --combo_cost 10 --cumulative_constraint --seven  -d --singlepenalty 1000000000000 -l
single node disjunction penalty is 1000000000000
added 11 disjunctions, one per node
WARNING: Logging before InitGoogleLogging() is written to STDERR
I0613 05:40:09.771340  1018 routing.cc:2833] All Unperformed Solution (11000000000000, time = 2 ms, memory used = 128.65 MB)
I0613 05:40:09.771448  1018 search.cc:252] Start search (memory used = 128.65 MB)
I0613 05:40:09.772099  1018 search.cc:252] Root node processed (time = 0 ms, constraints = 340, memory used = 128.65 MB)
I0613 05:40:09.773257  1018 search.cc:252] Solution #0 (10000000000060, time = 1 ms, branches = 44, failures = 0, depth = 33, memory used = 128.69 MB)
I0613 05:40:09.773905  1018 search.cc:252] Solution #1 (10000000000006, objective maximum = 10000000000060, time = 2 ms, branches = 47, failures = 2, depth = 33, Relocate<1>, neighbors = 1, filtered neighbors = 1, accepted neighbors = 1, memory used = 128.69 MB)
I0613 05:40:09.777364  1018 search.cc:252] Solution #2 (9000000000066, objective maximum = 10000000000060, time = 5 ms, branches = 51, failures = 5, depth = 33, MakeActiveOperator, neighbors = 50, filtered neighbors = 3, accepted neighbors = 2, memory used = 128.69 MB)
I0613 05:40:09.778257  1018 search.cc:252] Solution #3 (8000000000076, objective maximum = 10000000000060, time = 6 ms, branches = 54, failures = 7, depth = 33, MakeActiveOperator, neighbors = 51, filtered neighbors = 4, accepted neighbors = 3, memory used = 128.69 MB)
I0613 05:40:09.779109  1018 search.cc:252] Solution #4 (7000000000086, objective maximum = 10000000000060, time = 7 ms, branches = 59, failures = 9, depth = 33, MakeActiveOperator, neighbors = 52, filtered neighbors = 5, accepted neighbors = 4, memory used = 128.69 MB)
I0613 05:40:09.780122  1018 search.cc:252] Solution #5 (6000000000146, objective maximum = 10000000000060, time = 8 ms, branches = 62, failures = 12, depth = 33, MakeActiveOperator, neighbors = 58, filtered neighbors = 7, accepted neighbors = 5, memory used = 128.69 MB)
I0613 05:40:09.781003  1018 search.cc:252] Solution #6 (5000000000156, objective maximum = 10000000000060, time = 9 ms, branches = 66, failures = 14, depth = 33, MakeActiveOperator, neighbors = 59, filtered neighbors = 8, accepted neighbors = 6, memory used = 128.69 MB)
I0613 05:40:09.781849  1018 search.cc:252] Solution #7 (4000000000166, objective maximum = 10000000000060, time = 10 ms, branches = 69, failures = 16, depth = 33, MakeActiveOperator, neighbors = 60, filtered neighbors = 9, accepted neighbors = 7, memory used = 128.69 MB)
I0613 05:40:09.782863  1018 search.cc:252] Solution #8 (3000000000226, objective maximum = 10000000000060, time = 11 ms, branches = 75, failures = 19, depth = 33, MakeActiveOperator, neighbors = 66, filtered neighbors = 11, accepted neighbors = 8, memory used = 128.69 MB)
I0613 05:40:09.783536  1018 search.cc:252] Solution #9 (2000000000236, objective maximum = 10000000000060, time = 12 ms, branches = 78, failures = 21, depth = 33, MakeActiveOperator, neighbors = 67, filtered neighbors = 12, accepted neighbors = 9, memory used = 128.69 MB)
I0613 05:40:09.784235  1018 search.cc:252] Solution #10 (1000000000246, objective maximum = 10000000000060, time = 12 ms, branches = 82, failures = 23, depth = 33, MakeActiveOperator, neighbors = 68, filtered neighbors = 13, accepted neighbors = 10, memory used = 128.69 MB)
I0613 05:40:09.785501  1018 search.cc:252] Solution #11 (306, objective maximum = 10000000000060, time = 14 ms, branches = 85, failures = 26, depth = 33, MakeActiveOperator, neighbors = 74, filtered neighbors = 15, accepted neighbors = 11, memory used = 128.69 MB)
I0613 05:40:09.945478  1018 search.cc:252] Solution #12 (302, objective maximum = 10000000000060, time = 173 ms, branches = 4902, failures = 2863, depth = 33, PathLns, neighbors = 415, filtered neighbors = 282, accepted neighbors = 12, memory used = 128.69 MB)
I0613 05:40:10.231724  1018 search.cc:252] Solution #13 (252, objective maximum = 10000000000060, time = 460 ms, branches = 12422, failures = 7343, depth = 33, PathLns, neighbors = 1003, filtered neighbors = 722, accepted neighbors = 13, memory used = 128.69 MB)
I0613 05:40:10.244633  1018 search.cc:252] Solution #14 (248, objective maximum = 10000000000060, time = 473 ms, branches = 12562, failures = 7461, depth = 33, PathLns, neighbors = 1074, filtered neighbors = 755, accepted neighbors = 14, memory used = 128.69 MB)
I0613 05:40:10.543766  1018 search.cc:252] Finished search tree (time = 772 ms, branches = 18948, failures = 11532, neighbors = 2826, filtered neighbors = 1339, accepted neigbors = 14, memory used = 128.69 MB)
I0613 05:40:10.544117  1018 search.cc:252] End search (time = 772 ms, branches = 18948, failures = 11532, memory used = 128.69 MB, speed = 24544 branches/s)
The Objective Value is 248
Truck 0 travel time
     combo: 0
     single: 6
Truck 1 travel time
     combo: 70
     single: 0
Truck 2 travel time
     combo: 80
     single: 0
Truck 3 travel time
     combo: 80
     single: 0
Truck 4 travel time
     combo: 0
     single: 6
Truck 5 travel time
     combo: 0
     single: 6
```

With fake nodes flags, the wrong solution:

```
 python disjunction_fail.py  -v 5 --combo_cost 10 --cumulative_constraint --seven  -d --singlepenalty 1000000000000 -l --fake_nodes
[[0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [3, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000], [3, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000], [3, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000], [3, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000], [3, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000], [3, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000], [3, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000], [3, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000], [3, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000], [3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000], [3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000], [0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000], [0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000], [0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000], [0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000], [0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000], [0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000], [0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000], [0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000], [0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000], [0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000]]
single node disjunction penalty is 1000000000000
added 11 disjunctions, one per node
WARNING: Logging before InitGoogleLogging() is written to STDERR
I0613 05:40:50.159832  1026 search.cc:252] Start search (memory used = 128.64 MB)
I0613 05:40:50.160511  1026 search.cc:252] Root node processed (time = 0 ms, constraints = 397, memory used = 128.64 MB)
I0613 05:40:50.162806  1026 search.cc:252] Solution #0 (11000000080000, time = 2 ms, branches = 54, failures = 1, depth = 33, memory used = 128.64 MB)
I0613 05:40:50.164259  1026 search.cc:252] Solution #1 (11000000070000, objective maximum = 11000000080000, time = 4 ms, branches = 57, failures = 3, depth = 33, Relocate<1>, neighbors = 37, filtered neighbors = 1, accepted neighbors = 1, memory used = 128.64 MB)
I0613 05:40:50.165570  1026 search.cc:252] Solution #2 (11000000060000, objective maximum = 11000000080000, time = 5 ms, branches = 61, failures = 5, depth = 33, Relocate<1>, neighbors = 54, filtered neighbors = 2, accepted neighbors = 2, memory used = 128.64 MB)
I0613 05:40:50.166911  1026 search.cc:252] Solution #3 (11000000050000, objective maximum = 11000000080000, time = 6 ms, branches = 64, failures = 7, depth = 33, Relocate<1>, neighbors = 69, filtered neighbors = 3, accepted neighbors = 3, memory used = 128.64 MB)
I0613 05:40:50.167878  1026 search.cc:252] Solution #4 (11000000040000, objective maximum = 11000000080000, time = 7 ms, branches = 69, failures = 9, depth = 33, Relocate<1>, neighbors = 82, filtered neighbors = 4, accepted neighbors = 4, memory used = 128.64 MB)
I0613 05:40:50.168756  1026 search.cc:252] Solution #5 (11000000030000, objective maximum = 11000000080000, time = 8 ms, branches = 72, failures = 11, depth = 33, Relocate<1>, neighbors = 93, filtered neighbors = 5, accepted neighbors = 5, memory used = 128.64 MB)
I0613 05:40:50.169600  1026 search.cc:252] Solution #6 (11000000020000, objective maximum = 11000000080000, time = 9 ms, branches = 76, failures = 13, depth = 33, Relocate<1>, neighbors = 102, filtered neighbors = 6, accepted neighbors = 6, memory used = 128.64 MB)
I0613 05:40:50.170567  1026 search.cc:252] Solution #7 (11000000010000, objective maximum = 11000000080000, time = 10 ms, branches = 79, failures = 15, depth = 33, Relocate<1>, neighbors = 109, filtered neighbors = 7, accepted neighbors = 7, memory used = 128.64 MB)
I0613 05:40:50.171484  1026 search.cc:252] Solution #8 (11000000000000, objective maximum = 11000000080000, time = 11 ms, branches = 85, failures = 17, depth = 33, Relocate<1>, neighbors = 114, filtered neighbors = 8, accepted neighbors = 8, memory used = 128.64 MB)
I0613 05:40:50.188133  1026 search.cc:252] Solution #9 (10000000100010, objective maximum = 11000000080000, time = 28 ms, branches = 88, failures = 19, depth = 33, MakeActiveOperator, neighbors = 845, filtered neighbors = 9, accepted neighbors = 9, memory used = 128.64 MB)
I0613 05:40:50.189049  1026 search.cc:252] Solution #10 (9000000100020, objective maximum = 11000000080000, time = 29 ms, branches = 92, failures = 21, depth = 33, MakeActiveOperator, neighbors = 846, filtered neighbors = 10, accepted neighbors = 10, memory used = 128.64 MB)
I0613 05:40:50.189903  1026 search.cc:252] Solution #11 (8000000100030, objective maximum = 11000000080000, time = 29 ms, branches = 95, failures = 23, depth = 33, MakeActiveOperator, neighbors = 847, filtered neighbors = 11, accepted neighbors = 11, memory used = 128.64 MB)
I0613 05:40:50.191584  1026 search.cc:252] Solution #12 (7000000200040, objective maximum = 11000000080000, time = 31 ms, branches = 100, failures = 27, depth = 33, MakeActiveOperator, neighbors = 855, filtered neighbors = 14, accepted neighbors = 12, memory used = 128.64 MB)
I0613 05:40:50.192574  1026 search.cc:252] Solution #13 (6000000200050, objective maximum = 11000000080000, time = 32 ms, branches = 103, failures = 29, depth = 33, MakeActiveOperator, neighbors = 856, filtered neighbors = 15, accepted neighbors = 13, memory used = 128.64 MB)
I0613 05:40:50.193490  1026 search.cc:252] Solution #14 (5000000200060, objective maximum = 11000000080000, time = 33 ms, branches = 107, failures = 31, depth = 33, MakeActiveOperator, neighbors = 857, filtered neighbors = 16, accepted neighbors = 14, memory used = 128.64 MB)
I0613 05:40:50.195104  1026 search.cc:252] Solution #15 (4000000300070, objective maximum = 11000000080000, time = 35 ms, branches = 110, failures = 35, depth = 33, MakeActiveOperator, neighbors = 865, filtered neighbors = 19, accepted neighbors = 15, memory used = 128.64 MB)
I0613 05:40:50.195931  1026 search.cc:252] Solution #16 (3000000300080, objective maximum = 11000000080000, time = 36 ms, branches = 117, failures = 37, depth = 33, MakeActiveOperator, neighbors = 866, filtered neighbors = 20, accepted neighbors = 16, memory used = 128.64 MB)
I0613 05:40:50.196688  1026 search.cc:252] Solution #17 (2000000300090, objective maximum = 11000000080000, time = 36 ms, branches = 120, failures = 39, depth = 33, MakeActiveOperator, neighbors = 867, filtered neighbors = 21, accepted neighbors = 17, memory used = 128.64 MB)
I0613 05:40:50.198565  1026 search.cc:252] Solution #18 (1000000400100, objective maximum = 11000000080000, time = 38 ms, branches = 124, failures = 43, depth = 33, MakeActiveOperator, neighbors = 875, filtered neighbors = 24, accepted neighbors = 18, memory used = 128.64 MB)
I0613 05:40:50.199507  1026 search.cc:252] Solution #19 (400110, objective maximum = 11000000080000, time = 39 ms, branches = 127, failures = 45, depth = 33, MakeActiveOperator, neighbors = 876, filtered neighbors = 25, accepted neighbors = 19, memory used = 128.64 MB)
I0613 05:40:50.203441  1026 search.cc:252] Solution #20 (300160, objective maximum = 11000000080000, time = 43 ms, branches = 199, failures = 83, depth = 33, PathLns, neighbors = 879, filtered neighbors = 28, accepted neighbors = 20, memory used = 128.64 MB)
I0613 05:40:50.486515  1026 search.cc:252] Solution #21 (300156, objective maximum = 11000000080000, time = 326 ms, branches = 11300, failures = 6012, depth = 33, PathLns, neighbors = 1105, filtered neighbors = 232, accepted neighbors = 21, memory used = 128.64 MB)
I0613 05:40:50.612435  1026 search.cc:252] Solution #22 (200206, objective maximum = 11000000080000, time = 452 ms, branches = 15606, failures = 8379, depth = 33, PathLns, neighbors = 1299, filtered neighbors = 348, accepted neighbors = 22, memory used = 128.64 MB)
I0613 05:40:50.993079  1026 search.cc:252] Solution #23 (100256, objective maximum = 11000000080000, time = 833 ms, branches = 30421, failures = 16388, depth = 33, PathLns, neighbors = 1722, filtered neighbors = 671, accepted neighbors = 23, memory used = 128.64 MB)
I0613 05:40:51.339267  1026 search.cc:252] Solution #24 (306, objective maximum = 11000000080000, time = 1179 ms, branches = 42664, failures = 23056, depth = 33, PathLns, neighbors = 2118, filtered neighbors = 967, accepted neighbors = 24, memory used = 128.64 MB)
I0613 05:40:52.469370  1026 search.cc:252] Finished search tree (time = 2309 ms, branches = 79723, failures = 43611, neighbors = 6069, filtered neighbors = 2122, accepted neigbors = 24, memory used = 128.64 MB)
I0613 05:40:52.469784  1026 search.cc:252] End search (time = 2309 ms, branches = 79723, failures = 43611, memory used = 128.64 MB, speed = 34527 branches/s)
The Objective Value is 306
```

With 6 vehicles they both find the best solution (248).

I just don't know.




# License

Copyright 2019 James E. Marca

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
