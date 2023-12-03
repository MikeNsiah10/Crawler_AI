from flask import Flask, render_template, request, url_for
from whoosh.index import open_dir
from whoosh.qparser import QueryParser
import traceback

# Initialise Flask app
app = Flask(__name__)

# Directory where the Whoosh index is located
index_dir = 'whoosh_index'
index = open_dir(index_dir)

@app.route('/')
def home():
    # Render the HTML template for the search form
    return render_template('search_form.html', search_url=url_for('search'))

@app.route('/search')
def search():
    # Get the search query from the request parameters
    query = request.args.get('q', '')
    
    if not query:
        return 'No search query provided.'

    # Perform search and return search results
    with index.searcher() as searcher:
        query_parser = QueryParser("content", index.schema)
        query_obj = query_parser.parse(query)
        results = searcher.search(query_obj)
        

        return render_template('search_results.html', query=query, results=results)
#handle internal server error
@app.errorhandler(500)
def internal_error(exception):
    return "<pre>" + traceback.format_exc() + "</pre>"

if __name__ == '__main__':
    app.run(debug=True)
