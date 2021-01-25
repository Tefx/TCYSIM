1. Modelling the equipment
   1. Define Spec, Component and Equipment
   2. Define Request sand Operations
      1. Request:
         1. high-level
         2. submitted to blocks
         3. can be assigned to multiple equipment
      2. Operation:
         1. low_level
         2. generated for equipment
         3. contains detailed equipment moves
   3. Program the equipment:
      1. OpBuilder: Program the moves and operations
         1. build steps and define dependencies among steps
      2. ReqHandler: break requests to operations 
      3. JobScheduler: decide which requests or operations will be performed next
2. Define blocks and layout
   1. define dimensions
   2. define cells
   3. links equipment: one equipment can be shared among multiple blocks
   4. design yard layout: 
      1. block offset, lanes, equipment range
      2. rotate and transformation
      3. coordinate system
   5. ReqDispatcher: manage submitted requests and dispatch them to equipment
3. Setup Metrics
   1. probes
      1. TraceWriter
   2. Observer

Yard and Driver

1. Deploy blocks and equipments
2. (Optional) Extend Box
3. SpaceAllocator: allocate space for containers
4. BoxManager, AccessPoint...
5. Other roles (ProbeProcessor, Observer...)
6. (Optional) ExternalDriver
   1. PortEventGenerator
7. (Optional) PRC Server: integration with other tools

1. Analysis and Visualisation
   1. PlotItem, PlotSet
   2. TraceReader
   3. Demo visualiser
2. Utils
   1. IntervalTree
   2. Dispatcher
   3. IdxSet, RecentSet
   4. LoadPredicator
   5. KeyCache, TimeCache
   6. SingleLMP