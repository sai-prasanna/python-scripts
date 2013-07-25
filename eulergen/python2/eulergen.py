#!/usr/bin/python
"""Extracts Problem definitions from projecteuler.net and saves each to seperate
  file with common Python Template"""
import urllib2
import sys
from bs4 import BeautifulSoup


def main():

    if len(sys.argv) != 3:
<<<<<<< HEAD:eulergen.py
        print 'usage: ./eulergen.py <start problem> <end problem>'
=======
        print('usage: ./eulergen.py <start problem number> <end problem number>')
>>>>>>> daa80d6... Make Python 3 compatibile:eulergen/python2/eulergen.py
        sys.exit(1)

    start = int(sys.argv[1])
    end = int(sys.argv[2])

    for i in range(start, end + 1):
        url = ('http://projecteuler.net/problem=' + str(i))
        response = urllib2.urlopen(url)
        html = response.read()
        soup = BeautifulSoup(html)
        title = soup.h2.get_text()  # gets title
        file_name = str(i) + '_' + title.lower(
        ).replace(" ", "_").join('.py')  # lowercases it and removes whitespace

        problem_definition = '\n'.join(
            [tag.get_text() for tag in soup.find_all('p')])
        template = '''
#!/usr/bin/python
"""
%s
%s

"""


def main():


if __name__ == '__main__':
    main()

                    ''' % (title, problem_definition)
        f = open(filename, 'w')
        f.write(template)
        f.close()
        print('Created file %s succesfully' % filename)

if __name__ == '__main__':
    main()
