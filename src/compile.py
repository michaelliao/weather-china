'''
Created on Sep 8, 2010

@author: Michael Liao
'''

from os import path
from Cheetah.Template import Template

def main():
    file = path.join(path.split(__file__)[0], 'home.html')
    print 'Compile template %s...' % file
    cc = Template.compile(source=None, file=file, returnAClass=False, moduleName='autogen', className='CompiledTemplate')
    target = path.join(path.split(__file__)[0], 'autogen', '__init__.py')
    print 'Writing file %s...' % target
    f = open(target, 'w')
    f.write(cc)
    f.close()
    from autogen import CompiledTemplate
    CompiledTemplate(searchList=[])
    print 'Compiled ok.'

if __name__ == '__main__':
    main()
