Python bindings to the Rackspace Cloud Servers API
==================================================

Documentation forthcoming. 

In the meantime::

    >>> import cloudservers
    >>> cs = cloudservers.CloudServers(USERNAME, API_KEY)
    >>> cs.flavors.list()
    [...]
    >>> cs.servers.list()
    [...]
    >>> s = cs.servers.create(image=2, flavor=1, name='myserver')
    
    ... time passes ...
    
    >>> s.reboot()
    
    ... time passes ...
    
    >>> s.delete()
    
Or, from the shell, try ``cloudservers help``.

FAQ
===

What's wrong with libcloud?

    Nothing! However, as a cross-service binding it's by definition lowest
    common denominator; I needed access to the Rackspace-specific APIs (shared
    IP groups, image snapshots, resizing, etc.). I also wanted a command-line
    utility.
    
