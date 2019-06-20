# Bugs in disjunctions

This repo examines bugs in disjunctions.

The basic idea is that there are two variations of a single vehicle.
Variation 1 is the vehicle by itself, and variation 2 is the vehicle
with a trailer, which adds capacity but also brings an additional link
travel cost.


# Bug report, fixed

I worked all this up as a bug report, and you can see the original in
the git history, but it turns out there is an easy fix---just turn on
guided local search.

See my blog post for details at
https://activimetrics.com/blog/ortools/exploring_disjunctions/.


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
