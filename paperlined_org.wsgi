# This is a very thin layer that sits between the webserver (i.e. Apache) and the filesystem.
# My site is static for the most part, but we do a bit of dynamic work here only.
#
# Available at https://paperlined.org/ globally, or http://paperlined.localhost/ on my dev box.


import markdown, os, re
from datetime import datetime

WEBSITE_ROOT = '/var/www/paperlined.org/'

# this could be a separate file
HEADER = b'''
<!DOCTYPE html>
<html>
<head>
</head>
<body>
<div style="background-color:#88cccc; padding:0.5em; display:table-cell; box-shadow: 10px 10px 5px 0px rgba(0,0,0,0.75);">
    <a href="/" style="font-size:35px; font-weight:bold; color:#000!important; text-decoration:none">paperlined.org</a><br/>
    <span style="color:#777"><<DIRLIST>></span>
</div>
<!-- End of Header -->

'''

# Returns a list of the file path completely split apart.
# from https://www.oreilly.com/library/view/python-cookbook/0596001673/ch04s16.html
def splitall(path):
    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path: # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts

# actually it converts environ['PATH_INFO'], which is the latter part of the URL
def convert_URL_to_file_path(url):
    if url.find('/../') >= 0:       # Prevent security problems. (though I think that the browser
        return WEBSITE_ROOT         # and Apache both take care of this before it gets here)
    url = url[1:]                   # remove the leading slash, so we can start relative to WEBSITE_ROOT
    file_path = os.path.join(WEBSITE_ROOT, url)
    if os.path.isdir(file_path):    # it's either mod_autoindex or index.html
        if file_path[-1] != '/':
            file_path = file_path + '/'
        indexhtml = os.path.join(file_path, 'index.html')
        if os.path.exists(indexhtml):
            file_path = indexhtml
    return file_path


mime_types = { }
def parse_mime_types_line(line):
    #print(line)
    fields = line.split()
    for field in fields[1:]:
        mime_types[field] = fields[0]

# parse /etc/mime.types
def read_mime_types():
    with open('/etc/mime.types', 'r') as open_file:
        line = open_file.readline()
        while line:
            if re.match(r"^[a-zA-Z]", line):
                parse_mime_types_line(line.rstrip())
            line = open_file.readline()


# attach the cyan "paperlined.org" box that appears at the top of every page on this site
def generate_header(environ, file_path):
    dir_list = str.encode(environ['PATH_INFO']).split(b'/')
    dir_list.pop()      # drop the file name
    dir_list.pop(0)     # drop the initial backslash
    if environ['PATH_INFO'][-1] == '/' and len(dir_list) > 0:
        dir_list.pop()          # we don't need to link to our current directory
    url = b"/"
    dir_list_str = b""
    for dl in dir_list:
        url += dl + b"/"
        dir_list_str += b" &gt; <a href='" + url + b"'>" + dl + b"</a>"
    hdr = re.sub(b"<<DIRLIST>>", dir_list_str[6:], HEADER)
    if environ['PATH_INFO'] != '/' and file_path is not None:
        hdr += b'<div style="margin-left:4em; margin-top: 1em; margin-bottom:0.8em">document last updated on '
        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        hdr += str.encode(mtime.strftime("%b %e, %Y"))
        hdr += b'</div>'
    else:
        hdr += b'<br/>'
    return hdr


def serve_markdown_file(environ, start_response, file_extension, file_path, file_contents):
    if file_extension == "html" and file_contents[0:31] == b'<script src="/js/strapdown.js">':
        file_contents = file_contents[40:]
    file_contents = markdown.markdown(file_contents.decode('utf-8'))
    file_contents = "<link rel='stylesheet' href='/css/Python-Markdown.css' />" + file_contents
    file_contents = generate_header(environ, file_path) + str.encode(file_contents)
    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
    response_headers = [('Content-type', "text/html; charset=utf-8"),
                        ('Content-Length', str(len(file_contents))),
                        ('Last-Modified', mtime.strftime("%a, %e %b %Y %T GMT"))]
    start_response('200 OK', response_headers)
    return [file_contents]


def serve_file(environ, start_response, file_path):
    file_content_array = []
    size = 0
    with open(file_path, mode='rb') as file:
        while True:
            file_content_array.append(file.read())
            size += len(file_content_array[-1])
            if file_content_array[-1] == b'':
                break
            if size > 10*1024*1024:       # send at most the first 10mb of a file
                break
    file_extension = file_path.split('.')[-1].lower()
    file_contents = b''.join(file_content_array)
    if file_extension == 'md' or file_contents[0:31] == b'<script src="/js/strapdown.js">':
        return serve_markdown_file(environ, start_response, file_extension, file_path, file_contents)
    mime_type = mime_types[file_extension]
    if mime_type == 'text/html':
        file_contents = generate_header(environ, file_path) + file_contents

    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
    response_headers = [('Content-type', mime_type + "; charset=utf-8"),
                        ('Content-Length', str(len(file_contents))),
                        ('Last-Modified', mtime.strftime("%a, %e %b %Y %T GMT"))]
    start_response('200 OK', response_headers)
    return [file_contents]


def mod_autoindex(environ, start_response, file_path):
    # TODO: can we use the http://.../icons/ folder ourselves?
            # -> It might work now, but I doubt it will after we switch to AWS Lambda.

    output = "<h2>Index of " + environ['REQUEST_URI'] + "</h2>"
    files = os.listdir(file_path)
    for filename in files:
        path = os.path.join(file_path, filename)
        fname = splitall(path)[-1]
        if fname[0] == '.':         # skip dotfiles
            continue
        if os.path.isdir(path):
            output += "<a href='./" + fname + "/'>" + fname + "/</a><br/>\n"
        else:
            output += "<a href='./" + fname + "'>" + fname + "</a><br/>\n"

    output = generate_header(environ, None) + str.encode(output)
    response_headers = [('Content-type', 'text/html'),
                        ('Content-Length', str(len(output)))]
    start_response('200 OK', response_headers)
    return [output]


# redirect for example http://paperlined.org/apps to http://paperlined.org/apps/
def redirect_to_directory(environ, start_response, file_path):
    output = 'The document has moved <A HREF="' + environ['REQUEST_URI'] + '/">here</A>.<P>'

    output = str.encode(output)
    response_headers = [('Content-type',   'text/html'),
                        ('Content-Length', str(len(output))),
                        ('Location',       
                                #environ['REQUEST_SCHEME'] +        # "https"
                                #'://' +
                                #environ['SERVER_NAME'] +
                                environ['REQUEST_URI'] +
                                '/')                # <=== this is the most important line in this subroutine
                       ]
    start_response('301 Moved Permanently', response_headers)
    return [output]


def error_404_not_exist(environ, start_response, file_path):
    output = '<h3>Error: ' + environ['REQUEST_URI'] + ' not found</h3>'

    output = str.encode(output)
    response_headers = [('Content-type',   'text/html'),
                        ('Content-Length', str(len(output)))
                       ]
    start_response('404 Not Found', response_headers)
    return [output]


# This is the main WSGI function, called every time there's a request.
def application(environ, start_response):
    file_path = convert_URL_to_file_path(environ['PATH_INFO'])
    if not os.path.exists(file_path):
        return error_404_not_exist(environ, start_response, file_path)
    elif environ['PATH_INFO'][-1] != '/' and file_path[-1] == '/':    # redirect for example http://paperlined.org/apps to http://paperlined.org/apps/
        return redirect_to_directory(environ, start_response, file_path)
    elif os.path.isfile(file_path):
        return serve_file(environ, start_response, file_path)
    else:
        return mod_autoindex(environ, start_response, file_path)


read_mime_types()
#print(mime_types)
