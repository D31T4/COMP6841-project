'''
simulated SQL injection vulnerability using `eval`
'''

# simulated database
db: dict[str, str] = {
    'x': 1,
    'y': 1
}

def main(query: bytes):
    query = query.decode('utf-8')

    # simulated sql query
    result = eval(f'db.get("{query}", None)')
    print(result)
