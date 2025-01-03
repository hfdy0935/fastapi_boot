

from fastapi import HTTPException, Query, Request


def get_ua(request: Request):
    return request.headers.get('user-agent', '')


WHITE_LIST = ['abc', 'def']


def white_list_verify(identity: str = Query()):
    if identity not in WHITE_LIST:
        raise HTTPException(401)
    return identity
