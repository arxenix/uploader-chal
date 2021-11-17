from flask import Flask, request, redirect
from secrets import token_hex
import html
import json
import redis

app = Flask(__name__)
store = redis.Redis(host='redis', port=6379)

@app.post('/upload')
def upload():
    try:
        file_storage = request.files['file']
        mimetype = file_storage.mimetype.lower() or 'application/octet-stream'
        if 'script' in mimetype:
            mimetype = 'application/octet-stream'
        content = file_storage.read().decode('latin1')
        # dont DOS please
        if len(content) < 1024*1024:
            data = {
                'mimetype': mimetype,
                'content': content
            }
            filename = token_hex(16)
            store.set(filename, json.dumps(data), ex=300)
            return redirect(f'/uploads/{filename}', code=302)
    except:
        pass
    return 'Invalid Upload', 400

@app.get('/uploads/<filename>')
def get_upload(filename):
    data = store.get(filename)
    if data:
        data = json.loads(data)
        return data['content'].encode('latin1'), 200, {'Content-Type': data['mimetype']}
    else:
        return "Not Found", 404

@app.after_request
def headers(response):
    response.headers["Content-Security-Policy"] = "script-src 'self'; object-src 'none';"
    response.headers["X-Content-Type-Options"] = 'nosniff'
    return response

@app.get('/')
def main():
    return '''
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8" />
        <title>uploader</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.4.1/semantic.min.css" integrity="sha512-8bHTC73gkZ7rZ7vpqUQThUDhqcNFyYi2xgDgPDHc+GXVGHXq+xPjynxIopALmOPqzo9JZj0k6OqqewdGO3EsrQ==" crossorigin="anonymous" referrerpolicy="no-referrer" />
      </head>
      <body class="vsc-initialized">
        <div class="ui main text container">
          <h1 class="ui header">Uploader</h1>
          <p>Goal: get XSS on this origin in chrome stable</p>
          <p>DM your solution to <a href="https://twitter.com/ankursundara">@ankursundara</a> on Twitter or arxenix#1337 on Discord</p>
          <p><a href="/src">Server source</a></p>
          <p>Rules: don't attack other origins, no self-xss, don't DOS</p>
          <form class="ui form" action="/upload" method="POST" enctype="multipart/form-data">
            <label for="file">Select file:</label>
            <input type="file" id="file" name="file"><br><br>
            <button class="ui button" type="submit">Submit</button>
          </form>

          <br/>
          <br/>
          <h2 class="ui header">Hall of Fame</h2>
          <div id="hof"></div>
        </div>
        <script src="index.js"></script>
      </body>
    </html>
    '''

@app.get('/index.js')
def js():
    return '''
    /* this is NOT part of the actual challenge, just for updating leaderboard */
    (async ()=>{
        window.hof.innerHTML = await (await fetch('https://hc.lc/upload_hof.php')).text();
    })();
    ''', 200, {'Content-Type': 'application/javascript'}

@app.get('/src')
def src():
    s = '<h2>app.py</h2>\n<br><br>\n<pre>\n'
    with open('app.py') as f:
        s += html.escape(f.read())
    s += '</pre>'
    return s