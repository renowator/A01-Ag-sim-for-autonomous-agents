from ag_sim.server import server
import os
import sys
# To work on linux and Windows

sys.setrecursionlimit(915000)
if os.name == 'nt':
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
server.launch()
