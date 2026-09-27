import time, traceback, re, yaml, socket, pytz, inspect, discord, string, logging
import asyncio, os, importlib, glob, random, sys, datetime, shutil, signal
from os.path import exists, join, basename
from copy import deepcopy

botCommandChar = '!'
file_path       = os.path.realpath(os.path.abspath(inspect.getfile(inspect.currentframe())))
path            = os.path.realpath(os.path.abspath(os.path.join(file_path, os.pardir,os.pardir,)))
timezone        = pytz.utc
os.chdir(path)


savepath        = join(path, 'Save-State')
history_folder  = join(savepath, 'History')
backup_folder   = join(path, 'Backups')
# shutil.rmtree(savepath, ignore_errors=True)
if not exists(savepath): os.mkdir(savepath)
if not exists(backup_folder): os.mkdir(backup_folder)
print(savepath, path)

serverName      = "Nomic VIII PTR"
speed_mult      = 1
startDate       = datetime.datetime( year =2026, month = 9, day = 28-7, hour = 2, minute=0, tzinfo=timezone)
logFile         = 'Nomitorn_Log.txt' 

history_mode    = next((arg.split('=', 1)[1] for arg in sys.argv if arg.startswith('--history=')), 'strict')

SAVE_TO_FOLDER  = '_SAVE TO FOLDER SAVE FLAG'
OIK             = 'Object Index Key'
HISTORY_KEY     = 'HISTORY_KEY.yaml'
HISTORY_IGNORE  = [('Schedules',), ('Vars', 'Time')]

'''
Implement Modules By Placing Module Python File In Same Directory
Modules Must Have Different Names And Be Written With Python 3 Compatibility.
Use Blank.py as a Template for new modules.

It is recommended not to edit this file.
'''

class Object: pass
class DiscordNomicBot():

    """
    Initialize The Bot Handling Class  (Updated to Nomitron 4)
    """
    def __init__(self, ): # Done

        # Debug Logger Setup
        self.logger = logging.getLogger('Assistant logger')
        self.logger.setLevel(level=logging.DEBUG)
        fh = logging.StreamHandler()
        fh2 = logging.FileHandler(join( path, logFile), 'a', 'utf-8')
        fh_formatter = logging.Formatter('%(asctime)s %(levelname)s \t- %(message)s')
        fh.setFormatter(fh_formatter)
        fh2.setFormatter(fh_formatter)
        self.logger.addHandler(fh)
        self.logger.addHandler(fh2)

        # Constants
        self.sec = datetime.timedelta(seconds=1)
        self.min = datetime.timedelta(seconds=60)
        self.hr  = datetime.timedelta(seconds=3600)
        self.day = datetime.timedelta(days=1)
        self.week = datetime.timedelta(days=7)

        self.SAVE_TO_FOLDER = SAVE_TO_FOLDER
        self.last_save_time   = self.now()
        self.last_backup_time = self.now()

        self.ServerName = serverName
        self.stage_source = "Unknown"

        self.lock = False
        self.OIK = OIK

        # Functions and structures
        self.Data    = dict()                  # databases set
        self.DataNew = dict()
        self.Data_Changes     = []          # queued nested-data changes
        self.Data_Removes_IDs = []

        self.Tasks = list()                 # Tasks to funcation Call
        self.Obj_Refs = {}                  # Object references
        self.Modules = {}                   # Imported Modules

        self.hasSchedulerWarn = self.now() - 10*self.sec

        try:
            loop       = asyncio.new_event_loop()
            token      = open(join(path, 'Core', 'token.secret'),'r').readlines()[0].strip()
            self.discord    = discord
            self.client     = self.discord.Client(loop = loop, heartbeat_timeout=60*10, intents=self.discord.Intents.all())
            self.commandTree = self.discord.app_commands.CommandTree(self.client )                                                                
            self.log("   Discord Version:", self.discord.__version__)
            self.log("   Using Token: ..." + token[-6:])

        except ImportError:
            print("Discord Library Not Found, install by \"pip install discord\"")
            sys.exit(0)

        if not exists(backup_folder): os.mkdir(backup_folder)

        self.log(f"Starting Nomitron 6\n",
              f"  System Time: {self.now()}\n",
              f"  Host: {socket.gethostname()}\n"
              )
       
        self.load_dict_from_yaml()
        self.reload_modules()
        self.check_history()

        @self.client.event
        async def on_ready(): await self.wrap( self.on_ready )

        @self.client.event
        async def on_message(message): await self.Modules['Discord_Module'].on_message_event(self, message)

        @self.client.event
        async def on_raw_reaction_add(reaction): await self.Modules['Discord_Module'].on_raw_reaction_event(self, reaction, 'add')

        @self.client.event
        async def on_raw_reaction_remove(reaction): await self.Modules['Discord_Module'].on_raw_reaction_event(self, reaction, 'remove')

        @self.client.event
        async def on_member_update(before, after): await self.Modules['Discord_Module'].on_member_update_event(self, before, after)

        @self.client.event
        async def on_member_join(event): await self.Modules['Discord_Module'].on_member_join_event(self, event)

        @self.client.event
        async def on_raw_typing(event): await self.Modules['Discord_Module'].on_raw_typing(self, event)

        @self.client.event
        async def on_guild_channel_create(event): await self.Modules['Discord_Module'].on_guild_channel_mkrm(self, event)

        @self.client.event
        async def on_guild_channel_delete(event): await self.Modules['Discord_Module'].on_guild_channel_mkrm(self, event)

        @self.client.event
        async def on_guild_channel_update(before, after): await self.Modules['Discord_Module'].on_guild_channel_edit(self, before, after)

        # shutdown sequence
        signal.signal(signal.SIGTERM, lambda *args: signal.raise_signal(signal.SIGINT))
        self.client.run(token, reconnect=True, log_handler=None)
        self.log('Shutting down, saving')
        self.save_dict_to_yaml()

       
    """
    Get Now (Updated to Nomitron 6)
    """
    def now(self) -> datetime.datetime:
        t = datetime.datetime.now(timezone)
        # t = datetime.datetime(t.year, t.month, t.day, t.hour, t.minute, t.second, t.microsecond, tzinfo = timezone)
        t = startDate + ((t - startDate) * speed_mult)
        return t

    """
    Log to SDOUT (Updated to Nomitron 6)
    """
    def log(self, *args, mode='debug'): 
        mode = mode.lower()
        if   mode == 'debug': self.logger.debug( ' '.join([str(s) for s in args]))
        elif mode == 'info':  self.logger.info( ' '.join([str(s) for s in args]))
        elif mode == 'error': self.logger.error( ' '.join([str(s) for s in args]))
        elif mode == 'warn':  self.logger.warning( ' '.join([str(s) for s in args]))
        elif mode == 'warning':  self.logger.warning( ' '.join([str(s) for s in args]))
        else: self.logger.info( ' '.join([str(s) for s in args]))

        if mode == 'error' and self.has('Servers',self.ServerName) and self.get('Servers',self.ServerName,'SID') is not None: 
            text = ' '.join([str(s) for s in args])
            if len(text) > 1900: text = text[:1900]
            self.add_Task(
                 self.Modules['Discord_Module'].send,
                 {'bot':self, 'target':"mod-spam", 'content': text}
            )
       
    """
    Load/Save Memory Data From File (Updated to Nomitron 6), need other instance save/load
    """
    def save_dict_to_yaml(self, *args, **kwargs):
        """Save a dictionary as a directory tree of YAML files.

        Each ordinary key is saved as ``<key>.yaml`` and the file contains that
        key's value.  A dictionary containing ``SAVE_TO_FOLDER: True`` is instead
        saved as a directory named after its key; the marker itself is structural
        and is therefore not written to disk.  Marked dictionaries may themselves
        contain further marked dictionaries.
        """
        folder = os.path.abspath(savepath)

        def save_mapping(mapping, destination):
            os.makedirs(destination, exist_ok=True)
            for key, value in mapping.items():
                if key == SAVE_TO_FOLDER and mapping.get(SAVE_TO_FOLDER) is True:
                    continue
                if isinstance(value, dict) and value.get(SAVE_TO_FOLDER) is True:
                    save_mapping(value, join(destination, key))
                else:
                    with open(join(destination, f'{key}.yaml'), 'w', encoding='utf-8') as handle:
                        yaml.safe_dump(value, handle, allow_unicode=True, sort_keys=False)

        self._write_history()
        if self.now() - self.last_backup_time > self.day:
            shutil.copytree(folder, join(backup_folder, self.now().strftime("%Y-%m-%d %H:00")), dirs_exist_ok=True)
            self.last_backup_time = self.now()

        save_mapping(self.Data, folder)
        with open(join(folder, HISTORY_KEY), 'w', encoding='utf-8') as handle:
            yaml.safe_dump(getattr(self, '_last_commit_id', None), handle)
        self.last_save_time = self.now()

    def load_dict_from_yaml(self):
        """Load a dictionary previously written by :func:`save_dict_to_yaml`.

        Directories are restored as dictionaries with ``SAVE_TO_FOLDER: True``.
        Files must have the ``.yaml`` extension and are restored under their file
        name without that extension.
        """
        folder = os.path.abspath(savepath)
        if not os.path.isdir(folder):
            raise FileNotFoundError(f'Save folder does not exist: {folder}')

        def load_mapping(source):
            result = {}
            for entry in sorted(os.scandir(source), key=lambda item: item.name):
                if entry.is_dir():
                    if entry.name == 'History':
                        continue
                    result[entry.name] = load_mapping(entry.path)
                    result[entry.name][SAVE_TO_FOLDER] = True
                elif entry.is_file() and entry.name.endswith('.yaml'):
                    if entry.name == HISTORY_KEY:
                        continue
                    key = entry.name.replace('.yaml','')
                    if key in result:
                        raise ValueError(f'A YAML file and folder share the key {key!r} in {source}')
                    with open(entry.path, 'r', encoding='utf-8') as handle:
                        result[key] = yaml.safe_load(handle)
            return result

        self.Data.update(load_mapping(folder))

    # ------------------------------------------------------------------
    # Deferred nested-data changes
    # ------------------------------------------------------------------
    def stage(self, nested_key, method, *args, **kwargs):
        """Queue a replayable mutation without changing ``self.Data``.

        ``nested_key`` is a tuple/list of keys from ``self.Data`` to the
        affected value.  Names without a leading period are predefined
        operations. Names beginning with a period invoke that method on the
        target datatype, allowing arbitrary datatype methods to be replayed.

        Examples::

            bot.stage(('Players', 'Alice', 'Score'), 'set', 10)
            bot.stage(('Players', 'Alice', 'Items'), '.append', 'Sword')
            bot.stage(('Players', 'Alice', 'Tags'), '.add', 'active')
            bot.stage(('Players', 'Alice'), 'delete')
        """
        if not isinstance(method, str):
            raise TypeError('method must be a replayable method name string')

        if not isinstance(nested_key, (tuple, list)):
            nested_key = (nested_key,)
        nested_key = tuple(nested_key)

        predefined = {
            'set', 'delete', 'increment', 'decrement', 'append', 'remove',
            'merge', 'replace', 'multiply', 'divide', 'power_of', 'union',
            'update_nested_dict',
        }
        if not method.startswith('.') and method not in predefined:
            raise ValueError(f'Unknown staged operation {method!r}; datatype methods must start with "."')

        if not isinstance(self.Data_Changes, list):
            # Supports bots constructed from an older saved/runtime layout.
            self.Data_Changes = []
        if 'args' in kwargs: args = list(args) + kwargs.pop('args')
        self.Data_Changes.append({
            'source': self.stage_source,
            'operation': method,
            'path': nested_key,
            'args': deepcopy(args),
            'kwargs': deepcopy(kwargs),
            'sequence': len(self.Data_Changes),
        })
    def merge_commit(self, message=''):
        """Atomically apply staged changes and log them.

        A commit is stored as one human-readable journal entry. Journal files
        are rotated by a one-month span or 500 commits.
        """
        if not isinstance(self.Data_Changes, list):
            raise TypeError('self.Data_Changes must be a list of staged changes')
        if not self.Data_Changes:
            return []

        changes = self.Data_Changes
        committed = []
        base_state = deepcopy(self.Data)
        commit_time = self._next_history_key()
        for change in changes:
            record = {
                'operation': change['operation'],
                'path': list(change['path']),
                'args': deepcopy(change.get('args', ())),
                'kwargs': deepcopy(change.get('kwargs', {})),
                'source': change['source'],
            }
            try:
                yaml.dump(self._journal_value(record), Dumper=getattr(yaml, 'CSafeDumper', yaml.SafeDumper))
                self._apply_data_change(self.Data, change)
            except Exception as e:
                self.log(f"!!! Error In merge_commit: skipped {record['operation']} {record['path']} from {record['source']}: {e!r}", mode='error')
                # Undo anything the failed change half-applied.
                self.Data.clear()
                self.Data.update(deepcopy(base_state))
                for done in committed: self._apply_data_change(self.Data, done)
                continue
            committed.append(record)

        self.Data_Changes = []
        if not committed:
            return []
        commit = {
            'id': commit_time,
            'time': commit_time,
            'source': self.stage_source,
            'message': message,
            'changes': committed,
        }
        self._append_history_commit(commit, base_state)
        return committed
    
    def rebuild_state(self, *, until=None, errors=None):
        """Rebuild a logical data state from root and nested histories.

        Commits are replayed in the order they were written, not by time, since
        test runs with a different ``startDate`` put earlier times later on.
        ``until`` accepts a commit id, or a history timestamp, and rebuilds
        through that commit. If ``errors`` is a list, changes that fail to
        replay, and journal files that don't start where the previous one
        ended, are recorded there instead of raising.
        History is stored exclusively in the external journal, plus commits
        queued since the last save.
        """
        journals = self._journal_files()
        if getattr(self, '_pending_commits', None):
            journals.append(('<not yet saved>', {'base': self._journal_value(self._pending_base), 'commits': self._pending_commits}))
        if not journals:
            return {}
        rebuilt = deepcopy(journals[0][1].get('base', {}))
        ids = {str(commit['id']) for _, journal in journals for commit in journal['commits']}

        for index, (filename, journal) in enumerate(journals):
            if index and errors is not None:
                gaps = []
                self._find_data_differences(tuple(), self._comparable(rebuilt), self._comparable(journal.get('base', {})), gaps)
                if gaps:
                    errors.append(f"{basename(filename)} starts from a different state than the journal before it ends with, at {[list(d['path']) for d in gaps[:5]]}")
            for commit in journal['commits']:
                if until is not None and str(until) not in ids and str(commit['time']) > str(until):
                    return rebuilt
                for change in commit.get('changes', []):
                    try:
                        self._apply_data_change(rebuilt, change)
                    except Exception as e:
                        if errors is None: raise
                        errors.append(f"{basename(filename)} commit {commit['id']}: {change.get('operation')} {change.get('path')} failed: {e!r}")
                if until is not None and str(commit['id']) == str(until):
                    return rebuilt
        return rebuilt
    def compare_rebuild_to_current(self, rebuilt=None, *, base_state=None, until=None):
        """Return every path where a rebuilt state differs from current data.

        Paths in ``HISTORY_IGNORE`` and structural flags are not compared.
        """
        if rebuilt is None:
            rebuilt = self.rebuild_state(until=until)
        differences = []
        self._find_data_differences(tuple(), self._comparable(rebuilt), self._comparable(self.Data), differences)
        return differences

    def check_history(self):
        """Check the saved state against the journal at startup.

        ``HISTORY_KEY.yaml`` names the last commit the saved state includes.
        Commits journaled after it (made after the last save) are applied on
        top, then the state is compared with a full rebuild. On a difference
        the bot logs it and exits, unless started with ``--history=ignore``
        (carry on), ``--history=accept-state`` (journal a correction so the
        history matches the saved state) or ``--history=accept-history``
        (replace the state with the rebuild).
        """
        journals = self._journal_files()
        commits = [commit for _, journal in journals for commit in journal['commits']]
        self._last_commit_id = commits[-1]['id'] if commits else None
        if not commits:
            self.log('History check: no journal yet, skipped')
            return

        key = None
        if exists(join(savepath, HISTORY_KEY)):
            with open(join(savepath, HISTORY_KEY), 'r', encoding='utf-8') as handle:
                key = yaml.safe_load(handle)
        errors = []
        ids = [str(commit['id']) for commit in commits]
        pending = []
        if key is not None and str(key) not in ids:
            errors.append(f'The saved state is from commit {key}, which is not in the journal')
        elif key is not None:
            pending = commits[ids.index(str(key)) + 1:]
        for commit in pending:
            for change in commit.get('changes', []):
                try:
                    self._apply_data_change(self.Data, change)
                except Exception as e:
                    errors.append(f"Commit {commit['id']} (after the last save): {change.get('operation')} {change.get('path')} failed: {e!r}")
        if pending:
            self.log(f'History check: applied {len(pending)} commit(s) made after the last save')

        rebuilt = self.rebuild_state(errors=errors)
        differences = self.compare_rebuild_to_current(rebuilt)
        for line in errors:
            self.log(f'History check: {line}', mode='warn')
        if not differences:
            self.log(f'History check: saved state matches the journal ({len(commits)} commits)')
            if pending: self.save_dict_to_yaml()
            return

        self.log(f'History check: {len(differences)} difference(s) between the saved state and the journal', mode='warn')
        for d in differences[:50]:
            self.log(f"  {list(d['path'])}\n      journal: {repr(d['rebuild'])[:300]}\n      saved:   {repr(d['current'])[:300]}", mode='warn')
        if len(differences) > 50:
            self.log(f'  ... and {len(differences) - 50} more', mode='warn')

        if history_mode == 'ignore':
            self.log('History check: continuing anyway (--history=ignore)', mode='warn')
        elif history_mode == 'accept-state':
            changes = []
            for d in differences:
                path = list(d['path'])
                if self.has(path): changes.append({'operation': 'set', 'path': path, 'args': [self.get(path)], 'kwargs': {}})
                else:              changes.append({'operation': 'delete', 'path': path, 'args': [], 'kwargs': {}})
                changes[-1]['source'] = 'History check (--history=accept-state)'
            commit_time = self._next_history_key()
            self._append_history_commit({
                'id': commit_time,
                'time': commit_time,
                'source': 'History check (--history=accept-state)',
                'message': 'Correction: accept the saved state',
                'changes': changes,
            }, rebuilt)
            self.log(f'History check: journaled {len(changes)} correction(s) to match the saved state', mode='warn')
        elif history_mode == 'accept-history':
            # The scheduler's own entries aren't journaled, so keep the saved ones.
            for path in HISTORY_IGNORE:
                if self.has(path):
                    self._apply_data_change(rebuilt, {'operation': 'set', 'path': path, 'args': [self.get(path, include_flags=True)]})
                else:
                    try: self._apply_data_change(rebuilt, {'operation': 'delete', 'path': path})
                    except (KeyError, IndexError, TypeError): pass
            self.Data.clear()
            self.Data.update(rebuilt)
            self.log('History check: replaced the saved state with the rebuild (--history=accept-history)', mode='warn')
        else:
            self.log('History check: exiting. Fix the journal or Save-State, or restart with '
                     '--history=ignore, --history=accept-state or --history=accept-history', mode='warn')
            sys.exit(1)
        self.save_dict_to_yaml()

    def get(self, *nested_key, include_flags=False):
        """Return an isolated copy of a value stored in ``self.Data``.

        State flags such as ``SAVE_TO_FOLDER`` are removed recursively by
        default; pass ``include_flags=True`` to retain them.
        The returned object can be modified freely without changing the live
        game state. Use :meth:`stage` to queue a change.
        """
        if len(nested_key) == 1 and isinstance(nested_key[0], (tuple, list)):
            nested_key = tuple(nested_key[0])

        value = self._data_value_at(self.Data, tuple(nested_key))
        if not include_flags:
            value = self._without_flags(value)
        return value
    def get_Ref(self, *nested_key):
        """Return the live non-serializable object stored in ``self.Obj_Refs``.

        References intentionally are not copied: Discord client objects cannot
        reliably be deep-copied or serialized, and callers need the original
        object to invoke Discord methods on it.
        """
        if len(nested_key) == 1 and isinstance(nested_key[0], (tuple, list)):
            nested_key = tuple(nested_key[0])
        return self._data_value_at(self.Obj_Refs, tuple(nested_key))
   
    def set(self, nested_key, kwargs):
        """Stage any value at a nested path.

        Missing dictionary levels in the path are created when the staged
        change is committed. ``kwargs`` is the value assigned by ``set``.
        """
        if len(nested_key) == 1 and isinstance(nested_key[0], (tuple, list)):
            nested_key = tuple(nested_key[0])
        if not nested_key:
            raise ValueError('set requires at least one nested key')

        self.stage(nested_key, 'set', kwargs)
        return deepcopy(kwargs)
    def set_ObjRef(self, *nested_key_and_value):
        """Store a non-serializable object outside ``self.Data``.

        The final argument is the object and every preceding argument forms
        its path in ``self.Obj_Refs``.
        """
        if len(nested_key_and_value) < 2:
            raise ValueError('set_ObjRef requires a path and an object')
        *path, value = nested_key_and_value
        if len(path) == 1 and isinstance(path[0], (tuple, list)):
            path = list(path[0])
        if not path:
            raise ValueError('set_ObjRef requires at least one path key')

        parent, key = self._parent_and_key(self.Obj_Refs, tuple(path), create=True)
        parent[key] = value

    def remove(self, *nested_key):
        """Stage deletion of a nested data value.
        """
        if len(nested_key) == 1 and isinstance(nested_key[0], (tuple, list)):
            nested_key = tuple(nested_key[0])
        if not nested_key:
            raise ValueError('remove requires at least one nested key')
        if self.has(nested_key):
            self.stage(nested_key, 'delete')
    def remove_ObjRef(self, *nested_key):
        """Remove a non-serializable object reference if it is present."""
        if len(nested_key) == 1 and isinstance(nested_key[0], (tuple, list)):
            nested_key = tuple(nested_key[0])
        if not nested_key:
            raise ValueError('remove_ObjRef requires at least one path key')
        try:
            parent, key = self._parent_and_key(self.Obj_Refs, tuple(nested_key))
            del parent[key]
        except (KeyError, IndexError, TypeError):
            pass

    def update_nested_dict(self, nested_key, structure):
        """Merge stored dictionary values into ``structure`` and stage the result.

        Values already stored at ``nested_key`` take precedence.  If the path
        does not exist, ``structure`` itself is staged there.
        """
        if not isinstance(structure, dict):
            raise TypeError('structure must be a dictionary')

        updated = deepcopy(structure)
        if self.has(nested_key):
            current = self.get(nested_key)
            if not isinstance(current, dict):
                raise TypeError('the value at nested_key must be a dictionary')
            updated.update(current)

        self.set(nested_key, kwargs=updated)
        return deepcopy(updated)
    
    @staticmethod
    def _data_value_at(data, path):
        value = data
        for key in path:
            value = value[key]
        return value

    @classmethod
    def _without_flags(cls, value):
        """Copy data while removing structural flags at every nesting level."""
        if isinstance(value, dict):
            return {
                deepcopy(key): cls._without_flags(child)
                for key, child in value.items() if key != SAVE_TO_FOLDER
            }
        if isinstance(value, list):
            return [cls._without_flags(child) for child in value]
        if isinstance(value, tuple):
            return tuple(cls._without_flags(child) for child in value)
        if isinstance(value, set):
            return {cls._without_flags(child) for child in value}
        return deepcopy(value)

    @staticmethod
    def _parent_and_key(data, path, create=False):
        if not path:
            return None, None
        parent = data
        for key in path[:-1]:
            if isinstance(parent, dict):
                if key not in parent:
                    if not create:
                        raise KeyError(key)
                    parent[key] = {}
                parent = parent[key]
            else:
                parent = parent[key]
        return parent, path[-1]

    @classmethod
    def _apply_data_change(cls, data, change):
        method = change.get('operation', change.get('method'))
        if method is None:
            raise ValueError('A staged change must have an operation')
        path = tuple(change['path'])
        args = deepcopy(change.get('args', ()))
        kwargs = deepcopy(change.get('kwargs', {}))

        if method in {'set', 'replace'}:
            if not args and 'value' in kwargs:
                args = (kwargs['value'],)
            if len(args) != 1:
                raise TypeError(f'{method!r} requires one value argument')
            if not path:
                if not isinstance(args[0], dict):
                    raise TypeError('The root Data value must remain a dictionary')
                data.clear()
                data.update(args[0])
                return
            parent, key = cls._parent_and_key(data, path, create=True)
            parent[key] = args[0]
           
            return

        if method == 'delete':
            if not path:
                raise ValueError('The root Data dictionary cannot be deleted')
            parent, key = cls._parent_and_key(data, path)
            del parent[key]
            return

        if method in {'increment', 'decrement', 'multiply', 'divide', 'power_of'}:
            parent, key = cls._parent_and_key(data, path, create=True)

            if parent is None:
                raise ValueError('The root Data dictionary cannot be incremented or decremented')
            if len(args) != 1:
                raise TypeError(f'{method!r} requires one value argument')
            value = parent[key]
            if method == 'increment':
                parent[key] = value + args[0]
            elif method == 'decrement':
                parent[key] = value - args[0]
            elif method == 'multiply':
                parent[key] = value * args[0]
            elif method == 'divide':
                parent[key] = value / args[0]
            else:
                parent[key] = value ** args[0]
            return

        if method in {'append', 'remove', 'merge', 'union', 'update_nested_dict'}:
            parent, key = cls._parent_and_key(data, path,   create=True)
            if type(parent[key]) == dict:
                if key not in parent:
                    if method == 'append':
                        parent[key] = []
                    elif method == 'union':
                        parent[key] = set()
            target = cls._data_value_at(data, path)
            if method == 'append':
                try: target.append(args[0])
                except:
                    pass
            elif method == 'remove':
                parent, key = cls._parent_and_key(data, path)
                del parent[key]
            elif method in {'merge', 'update_nested_dict'}:
                if len(args) != 1 or not isinstance(args[0], dict) or not isinstance(target, dict):
                    raise TypeError(f'{method!r} requires a dictionary value and dictionary target')
                target.update(args[0])
            elif method == 'union':
                if not args:
                    raise TypeError("'union' requires an iterable value")
                if isinstance(target, set):
                    target.update(args[0])
                elif isinstance(target, dict):
                    target.update(args[0])
                else:
                    parent, key = cls._parent_and_key(data, path)
                    parent[key] = type(target)(set(target).union(args[0]))
            return

        if not method.startswith('.'):
            raise ValueError(f'Unknown predefined operation {method!r}')
        target = cls._data_value_at(data, path)
        operation = getattr(target, method[1:], None)
        if operation is None or not callable(operation):
            raise TypeError(f'{type(target).__name__} does not support staged method {method}')
        operation(*args, **kwargs)

    def _next_history_key(self):
        """Return a collision-free UTC datetime used as journal id and time."""
        current = self.now().astimezone(timezone)
        previous = getattr(self, '_last_history_time', None)
        if previous is not None and current <= previous:
            current = previous + datetime.timedelta(microseconds=1)
        self._last_history_time = current
        return current

    @staticmethod
    def _journal_value(value):
        if isinstance(value, dict):
            return {deepcopy(key): DiscordNomicBot._journal_value(child) for key, child in value.items()}
        if isinstance(value, (list, tuple)):
            return [DiscordNomicBot._journal_value(child) for child in value]
        if isinstance(value, set):
            return {DiscordNomicBot._journal_value(child) for child in value}
        return deepcopy(value)

    def _journal_files(self):
        """Return ``(filename, journal)`` for each journal with commits, oldest first."""
        journals = []
        if not os.path.isdir(history_folder):
            return journals
        for filename in glob.glob(join(history_folder, '*.yaml')):
            with open(filename, 'r', encoding='utf-8') as handle:
                journal = yaml.load(handle, Loader=getattr(yaml, 'CSafeLoader', yaml.SafeLoader)) or {}
            if journal.get('commits'):
                journals.append((filename, journal))
        return sorted(journals, key=lambda item: item[1]['commits'][0]['time'])

    @classmethod
    def _comparable(cls, data):
        """Copy ``data`` without flags or ``HISTORY_IGNORE`` paths, for comparing with a rebuild."""
        data = cls._without_flags(data)
        for path in HISTORY_IGNORE:
            try:
                parent, key = cls._parent_and_key(data, path)
                del parent[key]
            except (KeyError, IndexError, TypeError):
                pass
        return data

    def _append_history_commit(self, commit, base_state):
        """Queue a commit for the journal; save_dict_to_yaml writes queued commits along with the state."""
        if not getattr(self, '_pending_commits', None):
            self._pending_commits = []
            self._pending_base = base_state
        self._pending_commits.append(self._journal_value(commit))

    def _write_history(self):
        """Write queued commits to the journal. If the write fails they stay queued for the next save."""
        pending = getattr(self, '_pending_commits', None)
        if not pending:
            return
        os.makedirs(history_folder, exist_ok=True)
        filename, journal = getattr(self, '_history_cache', None) or (None, None)
        self._history_cache = None
        if filename is None or not exists(filename):
            filename, journal = None, None
            journals = self._journal_files()
            if journals:
                filename, journal = journals[-1]
        if not journal:
            journal = {'schema': 1, 'base': self._journal_value(self._pending_base), 'commits': []}

        commits = journal.setdefault('commits', [])
        if commits:
            first_time = commits[0]['time']
            span = pending[0]['time'] - first_time
            if (len(commits) >= 500 and span >= self.day) or span >= datetime.timedelta(days=30):
                journal = {'schema': 1, 'base': self._journal_value(self._pending_base), 'commits': []}
                filename = None
        journal['commits'].extend(pending)
        start = journal['commits'][0]['time']
        end = journal['commits'][-1]['time']
        new_filename = join(history_folder, f'{start:%Y%b%d}_to_{end:%Y%b%d}.yaml')
        temporary = new_filename + '.tmp'
        try:
            with open(temporary, 'w', encoding='utf-8') as handle:
                yaml.dump(journal, handle, Dumper=getattr(yaml, 'CSafeDumper', yaml.SafeDumper), allow_unicode=True, sort_keys=False)
        except Exception as e:
            self.log(f'Error writing journal to {temporary}: {e!r} ({len(pending)} commit(s) kept)', mode='error')
            if exists(temporary): os.remove(temporary)
            return
        os.replace(temporary, new_filename)
        self._history_cache = (new_filename, journal)
        self._pending_commits = []
        self._last_commit_id = pending[-1]['id']
        if filename and os.path.abspath(filename) != os.path.abspath(new_filename) and exists(filename):
            os.remove(filename)

    @classmethod
    def _find_data_differences(cls, path, rebuilt, current, differences):
        if isinstance(rebuilt, dict) and isinstance(current, dict):
            for key in sorted(set(rebuilt) | set(current), key=repr):
                if key not in rebuilt:
                    differences.append({'path': path + (key,), 'rebuild': '<missing>', 'current': deepcopy(current[key])})
                elif key not in current:
                    differences.append({'path': path + (key,), 'rebuild': deepcopy(rebuilt[key]), 'current': '<missing>'})
                else:
                    cls._find_data_differences(path + (key,), rebuilt[key], current[key], differences)
            return
        if rebuilt != current:
            differences.append({'path': path, 'rebuild': deepcopy(rebuilt), 'current': deepcopy(current)})

    # ------------------------------------------------------------------
    # Read-only nested-data helpers
    # ------------------------------------------------------------------
    def keys(self, *nested_key):
        """Return a copy of the keys at a nested ``self.Data`` value.

        For lists and tuples, this returns their indexes; callers that need
        contents can use ``get``. For dictionaries, it returns their keys.
        For sets, strings, and other containers, callers can use
        ``range(bot.len(...))``.
        """
        value = self.get(*nested_key)
        if isinstance(value, dict):
            return [
                deepcopy(key) for key in value.keys()
            ]
        if isinstance(value, (list, tuple)):
            return list(range(len(value)))
        raise TypeError(f'{type(value).__name__} does not have keys or items')

    def len(self, *nested_key):
        """Return the logical length of a nested ``self.Data`` value.

        Returns the ordinary length of the nested value.
        """
        value = self.get(*nested_key)
        if isinstance(value, dict):
            return len(value)
        return len(value)

    def has(self, *nested_key):
        """Return whether a complete nested key path exists in ``self.Data``."""
        if len(nested_key) == 1 and isinstance(nested_key[0], (tuple, list)):
            nested_key = tuple(nested_key[0])
        try:
            self._data_value_at(self.Data, tuple(nested_key))
        except (KeyError, IndexError, TypeError):
            return False
        return True

    def where(self, nested_key, conditional):
        """Return path of keys whose resolved values satisfy ``conditional``.

        ``nested_key`` must contain one or more ``'*'`` entries.  At each
        wildcard, every key in the dictionary reached by the preceding path is
        checked.  ``conditional`` receives an isolated copy of the final value.

        A single wildcard returns its matching keys; multiple wildcards return
        tuples of the matching wildcard keys.

        Example::

            bot.where(('Players', '*', 'Score'), lambda score: score >= 10)
            # -> ['Alice', 'Bob']
        """
        if not callable(conditional):
            raise TypeError('conditional must be a function that returns True or False')
        if not isinstance(nested_key, (tuple, list)):
            nested_key = (nested_key,)
        nested_key = tuple(nested_key)
        if '*' not in nested_key:
            raise ValueError("where path must contain at least one '*' wildcard")

        matches = []

        def walk(value, remaining_path, path_keys):
            if not remaining_path:
                if conditional(deepcopy(value)):
                    matches.append(deepcopy(path_keys))
                return

            key = remaining_path[0]
            if key == '*':
                if not isinstance(value, dict):
                    raise TypeError("'*' can only expand keys from a dictionary")
                for child_key, child_value in value.items():
                    walk(child_value, remaining_path[1:], path_keys + (child_key,))
            else:
                walk(value[key], remaining_path[1:], path_keys + (remaining_path[0],))

        walk(self.Data, nested_key, tuple())
        wildcard_count = nested_key.count('*')
        return matches

    """
    wrap a function call. (Updated to Nomitron 5)
    """   
    async def wrap(self, function, kwargs={}, args = [], timeout=None): # Done
        try: 
            st = time.time()
            if inspect.iscoroutinefunction(function): await function(**kwargs)
            else: function(*args, **kwargs)
            if timeout and time.time() - st > timeout:  
                self.log(f'!!! Error In {function.__name__}(kwargs={kwargs}): {datetime.datetime.now()} Function Call took longer then timeout of {timeout}',mode='wrap')
       
        except Exception as e: 
            traceback_str = ''.join(traceback.format_tb(e.__traceback__))
            self.log(f'!!! Error In {function.__name__}(kwargs={kwargs}): {datetime.datetime.now()} {e} \n{traceback_str}',mode='error')

            # raise e
       
    """
    Load all modules into Nomitron (Updated to Nomitron 5)
    """   
    def reload_modules(self):
        self.log('Importing Mods')

        for mod in list(glob.glob(join(path, "Modules", "*.py"))) + [file_path,]:
            modName = basename(mod)[:-3]
            if modName in ['Blank',]: continue
            self.log(f' Importing Module: {modName}', mode='Info')

            spec = importlib.util.spec_from_file_location(modName, mod)
            foo = importlib.util.module_from_spec(spec)
            self.Modules[modName] = foo
            spec.loader.exec_module(foo)

  
    """
    Add Task to Task List (Updated to Nomitron 6)
    """
    def add_Task(self, function, kwargs={}, name=None, timeout = 10):
        kwargs['bot'] = self
        if name is None: name = f"{function.__name__}"
        self.Tasks.append( dict(
            name=name,
            function=function,
            kwargs=kwargs,
            timeout = timeout) )
    
    async def _runTasks(self, commit_msg):
        while(self.lock): await asyncio.sleep(0.5)
        self.lock = True
        try:
            while len(self.Tasks) != 0:
                tasksToRun, self.Tasks = self.Tasks, list()
                for toDo in tasksToRun:
                    self.task_name = toDo['name']
                    self.stage_source = f"{toDo['name']} - {toDo['function']}({', '.join(toDo['kwargs'])})"
                    await self.wrap(toDo['function'], kwargs=toDo['kwargs'], timeout=toDo['timeout'])
                self.merge_commit(message=commit_msg)
        finally:
            self.lock = False
  
    """
    Scheduler Check Process (Updated to Nomitron 6)
    """
    # High Level Loop Functions. Only ones allowed to call RunTask 
    async def _CHECK_SCHEDULE(self):

        st = time.time()
        await self._runTasks(commit_msg=f"Uncaught Changes Scheduler Start - {self.now()}")

        par_toDo = {}
        seq_toDo ={}
        for name, sched in self.get('Schedules').items():
            # If Schedule To Be Executed
            if 'Mode' not in sched: self.log(sched.keys())
            if (sched['Mode'] == '==' and self.get(*sched['Key']) == sched['Trigger Value']) \
            or (sched['Mode'] == '!=' and self.get(*sched['Key']) != sched['Trigger Value']) \
            or (sched['Mode'] == '>=' and self.get(*sched['Key']) >= sched['Trigger Value']) \
            or (sched['Mode'] == '<=' and self.get(*sched['Key']) <= sched['Trigger Value']) \
            or (sched['Mode'] == '>'  and self.get(*sched['Key']) >  sched['Trigger Value']) \
            or (sched['Mode'] == '<'  and self.get(*sched['Key']) <  sched['Trigger Value']) \
            :
                # Run Event if sequantial only
                if sched["Sequential Only"]: seq_toDo[name] = self.Data['Schedules'].pop(name)
                else:                        par_toDo[name] = self.Data['Schedules'].pop(name)
        
        
        if seq_toDo or par_toDo: self.log('Scheduler:')
        for i,(k, sched) in enumerate(seq_toDo.items()): 
            if not hasattr(self.Modules.get(sched['Module Name']), sched['Method Name']):
                self.log(f"Scheduler Error:  - Seque. Sched: {k} - {sched['Module Name']}.{sched['Method Name']} not found.")
                continue
            func = getattr(self.Modules[sched['Module Name']], sched['Method Name'])
            kwargs = yaml.safe_load(sched['Kwargs'])
            kwargs.update(dict(bot = self))
            self.log(f"  - Seque. Sched: {k} - {sched['Module Name']}.{sched['Method Name']}")
            self.add_Task(function = func, kwargs=kwargs, name = f"{k}")
            await self._runTasks(commit_msg=f"Scheduler Sequential Sequence {self.get('Vars', 'Time')} - #{i}")

        for i, (k, sched) in enumerate(par_toDo.items()): 
            if not hasattr(self.Modules.get(sched['Module Name']), sched['Method Name']):
                self.log(f"Scheduler Error:  - Seque. Sched: {k} - {sched['Module Name']}.{sched['Method Name']} not found.")
                continue
            func = getattr(self.Modules[sched['Module Name']], sched['Method Name'])
            kwargs = yaml.safe_load(sched['Kwargs'])
            kwargs.update(dict(bot = self))         
            self.log(f"  - Async. Sched: {k} - {sched['Module Name']}.{sched['Method Name']}")
            self.add_Task(function = func, kwargs=kwargs, name = f"{k}")
        await self._runTasks(commit_msg=f"Scheduler Parallel Sequence {self.get('Vars', 'Time')}" )

        time_behind = self.now() -  self.get('Vars', 'Time')
        if time_behind.total_seconds() > 0 and not seq_toDo and not par_toDo:
            self.Data['Vars']['Time'] += 0.2*self.sec

        # Skip ahead in time simulation
        if time_behind > 15*self.sec * speed_mult and self.hasSchedulerWarn + self.sec*speed_mult < self.now(): 
            self.hasSchedulerWarn = self.now()
            minTime = self.now() + self.min
            self.log(f"Warning: SCHELURE IS RUNNING { int(time_behind.total_seconds()) } sec behind!! loop time: {time.time() - st}s", mode='Warning')
            for name, sched in self.get('Schedules').items():
                if list(sched['Key']) == ['Vars','Time'] and sched['Trigger Value'] < self.now() and minTime > sched['Trigger Value']:
                    minTime = sched['Trigger Value'] 
            if minTime < self.now(): self.Data['Vars']['Time'] = minTime - 1*self.sec

        if seq_toDo or par_toDo: self.log(f'Scheduler Done {self.Data['Vars']['Time']}')
        elif self.hasSchedulerWarn + 5 * self.sec * speed_mult < self.now(): 
            await asyncio.sleep(0.1)
    
    def schedule(self, module_name, method_name, Key, Mode, Trigger_Value, kwargs={}, name = None, sequential_only=False):
        if name is None: name = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        self.Data['Schedules'][name] = {
            'Key':Key,
            'Trigger Value':Trigger_Value,
            'Module Name': module_name, 
            'Method Name': method_name,
            'Kwargs': yaml.dump(kwargs).strip(),
            "Mode": Mode,
            "Sequential Only": sequential_only,
        }
    
   
    """
    Settup Bot on Target Server (Updated to Nomitron 6)
    """
    async def on_ready(self): # Done        
        self.log(' Logged in as ' + self.client.user.name)
 
        if startDate > self.now(): 
            while startDate > self.now(): 
                print("...Waiting For Nomic to start")
                time.sleep(30)

        self.add_Task(function = SETUP, kwargs={'bot':self})
        await self._runTasks(commit_msg=f"Startup setup - {self.now()}")

        self.add_Task(function = RELOAD_REFS, kwargs={'bot':self})
        await self._runTasks(commit_msg=f"Startup Reload Refs - {self.now()}")
        
        self.add_Task(function = UPDATE, kwargs={'bot':self})
        self.add_Task(function = UPDATE_DISPLAY, kwargs={'bot':self})
        await self._runTasks(commit_msg=f"Startup Update - {self.now()}")


        self.log(' Mainloop Start!')
        while 1: await self.wrap( self._CHECK_SCHEDULE )
            
        self.log('Exit of Loop')



"""
Pass a command to its respective module. (Updated to Nomitron 5)
"""   
def passToModule(bot, function_name, kwargs={}, timeout = 10): # Done
    task_name = f"{bot.task_name} > {function_name}" if getattr(bot, 'task_name', None) else None
    # Search For Duplicates Modules
    for name, mod in bot.Modules.items():
        if hasattr(mod, function_name):
            bot.add_Task( getattr(mod, function_name), kwargs=kwargs, name = task_name, timeout = timeout )



"""
Call all update functions in modules (Updated to Nomitron 5)
"""
async def SETUP(bot):
    bot.log(" Setup...")

    bot.update_nested_dict(('Schedules',), structure = {
    })
    bot.update_nested_dict(('Vars',), structure = {
        'Time': bot.now(),
        'Start Time': bot.now(),
    })
    bot.add_Task(function = passToModule, kwargs={'bot':bot, 'function_name':'setup',}, name = f"Setup On Ready {bot.now()}")

async def UPDATE(bot):
    await bot.wrap( passToModule, kwargs={'bot':bot, 'function_name':'update',})
    bot.schedule(
        name = 'Update and Save Loop',
        method_name = 'UPDATE',
        module_name = 'Nomitron',
        Key = ['Vars', 'Time'], Mode='>', Trigger_Value= bot.now() + 10*bot.sec*speed_mult, sequential_only=True
    )
    bot.add_Task(function = bot.save_dict_to_yaml, kwargs={}, name = f"Save Dict to YAML {bot.now()}")

async def RELOAD_REFS(bot):
    await bot.wrap( passToModule, kwargs={'bot':bot, 'function_name':'reload_references',})
    bot.schedule(
        name = 'Reload References Loop',
        method_name = 'RELOAD_REFS',
        module_name = 'Nomitron',
        Key = ['Vars', 'Time'], Mode='>', Trigger_Value= bot.now() + 10*bot.min*speed_mult, sequential_only=True
    )
  
async def UPDATE_DISPLAY(bot):
    await bot.wrap( passToModule, kwargs={'bot':bot, 'function_name':'update_display',})
    bot.schedule(
        name = 'Update Display Loop',
        method_name = 'UPDATE_DISPLAY',
        module_name = 'Nomitron',
        Key = ['Vars', 'Time'], Mode='>', Trigger_Value= bot.now() + 10*bot.sec*speed_mult, sequential_only=True
    )


if __name__ == '__main__':    
    print('\n\nLaunching Nomitron\n\n')
    bot = DiscordNomicBot()
