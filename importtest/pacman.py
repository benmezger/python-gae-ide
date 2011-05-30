#import lib
import new
libFile = open('lib.py')
libCode = libFile.read()
compiledLibCode = compile(libCode, "<string>", 'exec')
lib = new.module('lib')
exec compiledLibCode in lib.__dict__




def pac():
    pass

def main():
    print 'hello pacman'
    
if __name__ == '__main__':
    main()
