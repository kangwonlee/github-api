import ast
import datetime
import json
import tempfile
import urllib.parse as up

import pytest
import requests

import pyapi


@pytest.fixture(scope='module')
def get_auth():

    auth = pyapi.get_basic_auth()

    yield auth

    del auth


@pytest.fixture(scope='module')
def info():
    # test info
    with open('test_post_repo_commit_comment_info.txt', 'r') as f:
        info = [line.strip() for line in f.readlines()]

    return info


def test_get_repo_comments_public():
    result = pyapi.get_repo_pr_comments_public('octocat', 'Hello-World')
    # https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.at.html#pandas.DataFrame.at

    id = result.at[result.index[-1], 'id']
    url = result.at[result.index[-1], 'url']
    parse = up.urlparse(url)
    # sample : ParseResult(
    #               scheme='https',
    #               netloc='api.github.com',
    #               path='/repos/octocat/Hello-World/pulls/comments/124412547',
    #               params='', query='', fragment='')

    assert 'https' == parse.scheme
    assert parse.netloc.endswith('github.com')
    assert parse.path.endswith(str(id))


def test_url_repo_comments():
    owner = 'octocat'
    repo = 'Hello-World'

    parse = up.urlparse(pyapi.get_url_repo_pr_comments(owner, repo))

    assert 'https' == parse.scheme
    assert parse.netloc.endswith('github.com')
    assert owner in parse.path
    assert repo in parse.path


def test_get_url_delete_repo_commit_comment():
    owner = 'octocat'
    repo = 'Hello-World'
    comment_id = '6dcb09b5b57875f334f61aebed695e2e4193db5e'

    # function under test
    url = pyapi.get_url_delete_repo_commit_comment(owner, repo, comment_id)

    parse = up.urlparse(url)

    assert 'https' == parse.scheme
    assert parse.netloc.endswith('github.com')
    assert owner in parse.path
    assert repo in parse.path
    assert comment_id in parse.path


def test_req_to_df_unpack_dict():
    list_nested_dict = [
        {'a1': 'a1 str', 'b1': {'c1': 'b1.c1 str', 'd1': 'b1.d1 str'}},
        {'a2': 'a2 str', 'b2': {'c2': 'b2.c2 str', 'd2': 'b2.d2 str'}},
        {'a3': 'a3 str', 'b3': {'c3': 'b3.c3 str', 'd3': 'b3.d3 str'}},
        {'a4': 'a4 str', 'b4': {'c4': 'b4.c4 str', 'd4': 'b4.d4 str'}},
    ]

    result = pyapi.unpack_list_of_nested_dict(list_nested_dict)

    expected = [
        {'a1': 'a1 str', 'b1.c1': 'b1.c1 str', 'b1.d1': 'b1.d1 str'},
        {'a2': 'a2 str', 'b2.c2': 'b2.c2 str', 'b2.d2': 'b2.d2 str'},
        {'a3': 'a3 str', 'b3.c3': 'b3.c3 str', 'b3.d3': 'b3.d3 str'},
        {'a4': 'a4 str', 'b4.c4': 'b4.c4 str', 'b4.d4': 'b4.d4 str'},
    ]

    for row_result, row_expected in zip(result, expected):
        assert row_result == row_expected


def test_get_comment_utc_time():
    utc_time_str = '2011-04-14T16:00:49Z'

    # function under test
    result = pyapi.get_comment_utc_time(utc_time_str)

    expected = datetime.datetime(
        2011, 4, 14, hour=16, minute=0, second=49, tzinfo=datetime.timezone.utc)

    assert expected == result


def test_post_repo_commit_comment(get_auth, info):
    """
    Please run this test with disabling capture

    =======
    Example
    =======
    $ pytest -s tests
    """

    post_info = ast.literal_eval(info[-1])

    github = pyapi.GitHub(api_auth=get_auth)

    comment_str = 'test ok?'

    post_result = github.post_repo_commit_comment(
        owner=post_info['owner'],
        repo=post_info['repo'],
        sha=post_info['sha'],
        comment_str=comment_str,
    )

    assert post_result.ok, f'Not authorized {post_result}'

    response_dict = post_result.json()

    assert isinstance(response_dict, dict), type(response_dict)

    expected_keys = [
        "html_url", "url", "id", "node_id", "body", "path",
        "position", "line", "commit_id", "user", "created_at", "updated_at",
    ]
    assert all(key in response_dict for key in expected_keys), post_result

    # delete posted message
    delete_result = github.delete_repo_commit_comment(
        owner=post_info['owner'],
        repo=post_info['repo'],
        comment_id=response_dict['id'],
    )

    assert delete_result.ok, f'Not deleted: {delete_result}'

    # cleanup
    post_info['comment_str'] = comment_str
    cleanup_repo_commit_comments(github, post_info)


def test_post_repo_issue_comment(get_auth, info):
    """
    Please run this test with disabling capture

    =======
    Example
    =======
    $ pytest -s tests
    """

    post_info = ast.literal_eval(info[-2])

    github = pyapi.GitHub(api_auth=get_auth)

    post_result = github.post_repo_issue_comment(
        owner=post_info['owner'],
        repo=post_info['repo'],
        issue_number=post_info['issue_no'],
        comment_str='test ok?',
    )

    assert post_result.ok, f'Not authorized {post_result}'

    response_dict = post_result.json()

    assert isinstance(response_dict, dict), type(response_dict)

    expected_keys = [
        "id", "node_id", "url", "html_url", "body",
        "user", "created_at", "updated_at",
    ]
    assert all(key in response_dict for key in expected_keys), post_result


@pytest.fixture
def sample_todo_list():
    return pyapi.get_todo_list('sample_todo_list.json')


@pytest.fixture
def sample_todo_list_was_hr():
    return pyapi.get_todo_list('sample_todo_list_was_hr.json')


def test_get_todo_list(sample_todo_list, get_auth):

    # get temp file name
    with tempfile.NamedTemporaryFile(mode='wt') as temp_name:
        temp_file_name = temp_name.name

    # write to the temp file
    with open(temp_file_name, mode='wt') as temp_write:
        json.dump(sample_todo_list, temp_write)

    # open to test
    result = pyapi.get_todo_list(temp_file_name)
    assert len(result) == len(sample_todo_list)
    for result_dict, expected_dict in zip(result, sample_todo_list):
        assert result_dict == expected_dict


def test_GitHubToDo_constructor(sample_todo_list, get_auth):

    todo_processor = pyapi.GitHubToDo(
        todo_list=sample_todo_list,
        api_auth=get_auth,
    )

    assert hasattr(todo_processor, 'session')
    assert hasattr(todo_processor, 'todo_list')


def test_GitHubToDo_run_todo(sample_todo_list, get_auth):

    todo_processor = pyapi.GitHubToDo(
        todo_list=sample_todo_list,
        api_auth=get_auth,
    )

    response_list = todo_processor.run_todo()

    assert len(response_list) == len(sample_todo_list)

    for response, todo in zip(response_list, sample_todo_list):
        # print("response.keys() =", list(response.json().keys()))
        if isinstance(response, requests.Response):
            response_json = response.json()
            assert 'url' in response_json, (
                '\n'
                f"todo = {todo}\n"
                f"response.text = {response.text}\n"
                f"repr(response) = {repr(response)}"
            )

            response_url_parse = up.urlparse(response.json()['url'])
            assert response_url_parse.path.lower().startswith(
                ('/'.join(('', 'repos', todo['owner'], todo['repo'])).lower())), response.json()

    # cleanup
    # sample loop
    for sample_todo_dict in sample_todo_list:
        cleanup_repo_commit_comments(todo_processor, sample_todo_dict)


def cleanup_repo_commit_comments(github, sample_send_message_dict):
    get_message_response = github.get_repo_commit_comments(
        sample_send_message_dict['owner'],
        sample_send_message_dict['repo'],
        sample_send_message_dict['sha'],
    )

    get_message_list = get_message_response.json()

    # message loop
    for get_message_dict in get_message_list:
        assert isinstance(get_message_dict, dict), type(get_message_dict)

        if get_message_dict['body'] == sample_send_message_dict['comment_str']:
            delete_response = github.delete_repo_commit_comment(
                owner=sample_send_message_dict['owner'],
                repo=sample_send_message_dict['repo'],
                comment_id=get_message_dict['id']
            )

            assert delete_response.ok


def test_GitHubToDo_was_last_message_within_hours(sample_todo_list_was_hr, get_auth):

    todo_processor = pyapi.GitHubToDo(
        todo_list=sample_todo_list_was_hr,
        api_auth=get_auth,
    )

    owner = sample_todo_list_was_hr[0]['owner']
    repo = sample_todo_list_was_hr[0]['repo']
    sha = sample_todo_list_was_hr[0]['sha']
    body = sample_todo_list_was_hr[0]['comment_str']

    # post a message before test
    post_response = todo_processor.post_repo_commit_comment(
        owner, repo, sha, body)

    # function under test
    result = todo_processor.was_last_message_within_hours(
        sample_todo_list_was_hr[0],
        b_verbose=False,
        hr=0.5,
    )

    assert result

    post_response_dict = post_response.json()
    delete_response = todo_processor.delete_repo_commit_comment(
        owner=owner,
        repo=repo,
        comment_id=post_response_dict['id'],
    )

    assert delete_response.ok, delete_response

    cleanup_repo_commit_comments(todo_processor, sample_todo_list_was_hr[0])
