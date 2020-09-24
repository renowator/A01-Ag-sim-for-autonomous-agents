from ag_sim.server import server
import os
# To work on linux and Windows
if os.name == 'nt':
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
server.launch()
