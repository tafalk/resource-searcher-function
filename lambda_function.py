"""Resource Searcher"""
import os
import logging
import boto3
from boto3.dynamodb.conditions import Key, Attr

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """"Default Handler"""
    logger.debug(
        'fetching user interactions triggered event triggered with event %s', event)
    query_string = event.get('query')

    # DynamoDB connection and tables
    dynamodb = boto3.resource('dynamodb')
    user_table = dynamodb.Table(os.environ['USER_TABLE'])
    stream_table = dynamodb.Table(os.environ['STREAM_TABLE'])
    canto_table = dynamodb.Table(os.environ['CANTO_TABLE'])

    # variables
    user_preferred_name_attr = 'preferredName'
    user_username_attr = 'username'
    stream_title_attr = 'title'
    stream_body_attr = 'body'
    canto_body_attr = 'body'
    stream_is_sealed_attr = 'isSealed'

    # Scan and filter users
    user_scan_response = user_table.scan(
        Select='ALL_ATTRIBUTES',
        FilterExpression=Attr(user_username_attr).begins_with(query_string) | Attr(
            user_preferred_name_attr).begins_with(query_string)
    )

    stream_scan_response = stream_table.scan(
        Select='ALL_ATTRIBUTES',
        FilterExpression=Attr(stream_is_sealed_attr).eq(1)
    )

    canto_scan_response = canto_table.scan(
        Select='ALL_ATTRIBUTES'
    )

    user_items = user_scan_response['Items']
    stream_items = stream_scan_response['Items']
    canto_items = canto_scan_response['Items']

    # Add typename to be distinguished in AppSync Union
    for user_item in user_items:
        user_item.update({"typename": "User"})

    for stream_item in stream_items:
        stream_item.update({"typename": "Stream"})

    for canto_item in canto_items:
        canto_item.update({"typename": "Canto"})

    # filter stream scan
    stream_items = [x for x in stream_items if (x.get(stream_title_attr) is not None and query_string in x.get(
        stream_title_attr)) or (query_string in x.get(stream_body_attr))]

    # filter canto scan
    canto_items = [x for x in canto_items if (
        query_string in x.get(canto_body_attr))]

    # TODO: Order results (i.e. alphabetically for users, ??? for streams)

    return user_items + stream_items + canto_items
