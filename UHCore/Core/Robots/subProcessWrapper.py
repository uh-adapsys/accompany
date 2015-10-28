from multiprocessing import Process, Pipe, RLock, Queue
import inspect
import sys
import traceback

class SubProcessWrapper(object):
    def __init__(self, imports, className, *args, **kwargs):
        super(SubProcessWrapper, self).__init__()
        sendPipe, recvPipe = Pipe()
	object.__setattr__(self, '_sendPipe', sendPipe)
	object.__setattr__(self, '_recvPipe', recvPipe)
        object.__setattr__(self, '_pipeLock', RLock())
        object.__setattr__(self, '_wrapped_dict_', {})
        classData = {
                       'imports': imports,
                       'name': className,
                       'args': args,
                       'kwargs': kwargs
                       }

        startEvent = Queue()
	object.__setattr__(self, '_startEvent', startEvent)
        run = object.__getattribute__(self, '_run')
        proc = Process(target=run, args=(recvPipe, classData, startEvent))
        object.__setattr__(self, '_subprocess', proc)
        proc.daemon = True
        proc.start()
        d= startEvent.get()
        object.__setattr__(self, '_wrapped_dict_', d)
    
    def __del__(self):
        object.__getattribute__(self, '_sendPipe').close()
        object.__getattribute__(self, '_recvPipe').close()

    def __getattribute__(self, name):
        #if name[:1] == '_':
        #    print "Getting %s locally" % name
        #    return object.__getattribute__(self, name)
        #if name in object.__getattribute__(self, '_wrapped_dict_'):
        def wrappedFunc(*args, **kwargs):
            msg = {'name': name, 'args':args, 'kwargs':kwargs}
            return object.__getattribute__(self, '_send')(msg)
        if object.__getattribute__(self, '_wrapped_dict_')[name].endswith('method'):
            return wrappedFunc
        else:
            return wrappedFunc()
        
    def _run(self, recvPipe, classData, startEvent):
        # everything inside here is run in a separate process space
        try:
            for importStatement in classData['imports']:
                exec(importStatement, globals())
        except Exception as e:
            print >> sys.stderr, "%s\n%s" % (e, traceback.format_exc(e))
            recvPipe.send(e)
            return
        
        if classData['name'] in globals():
            classInstance = globals()[classData['name']](*classData['args'], **classData['kwargs'])
            wrappedDict = {}
            for k, v in inspect.getmembers(classInstance):
                if k.startswith('__'):
                    continue
                elif hasattr(type(classInstance), k):
                    wrappedDict[k] = type(getattr(type(classInstance), k)).__name__
                else:
                    wrappedDict[k] = type(getattr(classInstance, k)).__name__
            startEvent.put(wrappedDict)
        else:
            raise ValueError("Unable to create class %s in from current imports" % (classData['name'], ))
        while True:
            try:
                msg = recvPipe.recv()
            except EOFError:
                break
            except KeyboardInterrupt:
                break
            
            if not hasattr(classInstance, msg['name']):
                ret = AttributeError("'%s' object has no attribute '%s'" % (classData['name'], msg['name']))
            else:
                try:
                    func = getattr(classInstance, msg['name'])
                    if isinstance(type(func), property):
                        ret = func
                    elif callable(func):
                        ret = func(*msg.get('args', ()), **msg.get('kwargs', {}))
                    else:
                        ret = func
                except Exception as e:
                    print >> sys.stderr, "%s\n%s" % (e, traceback.format_exc())
                    ret = e
            recvPipe.send(ret)
            
    def _send(self, msg):
        lock = object.__getattribute__(self, '_pipeLock')
        lock.acquire()
        try:
            object.__getattribute__(self, '_sendPipe').send(msg)
            try:
                ret = object.__getattribute__(self, '_sendPipe').recv()
            except EOFError:
                return None
            
            if isinstance(ret, Exception):
                raise ret
            else:
                return ret
        except EOFError:
            return
        except KeyboardInterrupt:
            return
        finally:
            lock.release()

