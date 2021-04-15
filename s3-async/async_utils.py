import logging

host = 'http://localhost:8080/api/darkshield'


async def create_context(session, context, data):
  url = f'{host}/{context}.create'
  logging.info(f'POST: {url}')
  await session.post(url, json=data, raise_for_status=True)


async def destroy_context(session, context, name):
  url = f'{host}/{context}.destroy'
  logging.info(f'POST: {url}')
  await session.post(url, json={'name': name})
