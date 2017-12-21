import requests


def run_request(queries, exclude_urls=[]):
    result = []
    key = 'secret'

    for query in queries:
        api_result = requests.get(
            'https://api.datamarket.azure.com/Bing/SearchWeb/Web?Query=%27%22' + query + '%22%27&$format=json',
            auth=(key, key))
        if api_result.status_code == 200:
            json = api_result.json()['d']
            for i in json['results']:
                add_result(i, result, exclude_urls)

            # Get another page of results from the API, so each query can yield up to 100 results
            if len(json['results']) > 49 and json['__next'] is not None:
                api_result = requests.get(
                    json['__next'] + '&$format=json',
                    auth=(key, key))
                if api_result.status_code == 200:
                    json = api_result.json()['d']
                    for i in json['results']:
                        add_result(i, result, exclude_urls)

    return result


def add_result(api_row, result_list, excluded_urls):
    # Second 'and' is explained here: http://stackoverflow.com/questions/3897499/check-if-value-already-exists-within-list-of-dictionaries
    if api_row['Url'] not in excluded_urls and not any(dict.get('url', None) == api_row['Url'] for dict in result_list):
        result_list.append({'displayurl': api_row['DisplayUrl'], 'desc': api_row['Description'], 'url': api_row['Url'],
                            'title': api_row['Title']})

# Sort list; get top num_queries and return just the text
# chunks_with_scores is a list of tuples; each tuple is the chunk and its score
def build_query_result(chunks_with_scores, num_queries, source=''):
    sorted_chunks = sorted(chunks_with_scores, key=lambda score: score[1], reverse=True)[:num_queries]

    return {'success': True, 'data': [top_text[0] for top_text in sorted_chunks],
            'source': source}