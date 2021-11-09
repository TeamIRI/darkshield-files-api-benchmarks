import logging

# Append parent directory to PYTHON_PATH so we can import utils.py
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from server_config import hostname, port, is_https

host = f'http{"s" if is_https else ""}://{hostname}:{port}/api/darkshield'

async def create_context(session, context, data):
  url = f'{host}/{context}.create'
  logging.info(f'POST: {url}')
  await session.post(url, json=data, raise_for_status=True)


async def destroy_context(session, context, name):
  url = f'{host}/{context}.destroy'
  logging.info(f'POST: {url}')
  await session.post(url, json={'name': name})
