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
        print "Loaded..."
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
            print "Getting %s remote" % name
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
                if importStatement.startswith('import '):
                    for namespace in importStatement[7:].split(','):
                        globals()[namespace.strip()] = __import__(namespace.strip(), globals(), locals())
                elif importStatement.startswith('from '):
                    # from time import sleep
                    # from time import sleep, clock as ticker
                    namespace = importStatement[5: importStatement.index(' ', 5)]
                    fromlist = importStatement[importStatement.index(' ', 5) + 7:].strip()
                    for item in fromlist.split(','):
                        if item.strip() == '':
                            continue
                        if ' as ' in item:
                            itemName = item[:item.index(' as ')].strip()
                            asName = item[item.index(' as ') + 3:].strip()
                            temp = __import__(namespace, globals(), locals(), [itemName])
                            globals()[asName] = getattr(temp, itemName)
                        else:
                            temp = __import__(namespace, globals(), locals(), [item])
                            attr = getattr(temp, item)
                            globals()[item] = attr
                else:
                    raise ValueError("Unknown import statement '%s'" % importStatement)
        except Exception as e:
            print >> sys.stderr, "%s\n%s" % (e, traceback.format_exc(e))
            recvPipe.send(e)
            return
        
        if classData['name'] in globals():
            classInstance = globals()[classData['name']](*classData['args'], **classData['kwargs'])
            wrappedDict = dict([(k, 
                                 type(getattr(type(classInstance), k)).__name__) 
                                 for k, v in inspect.getmembers(classInstance)])
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

