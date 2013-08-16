# sed.py: A substitution plugin

import re
import traceback

from hooks import Hook

SED_REGEX = re.compile(r"^(?:(\S+)[:,] )?(?:(.+?)/)?s/(.+?)/(.*?)(?:/([gixs]{0,4}))?$")

def populate(sedobject, groups):
    group_types = ("target", "qual", "to_replace", "replacement", "flags")
    for k, v in zip(group_types, groups):
        setattr(sedobject, k, v)

def set_flags(sedobject, flags):
    i = 0
    count = 1

    if not flags:
        setattr(sedobject, 'flags', i)
        setattr(sedobject, 'count', count)
        return

    for item in flags:
        if item == 'i':
            i |= re.IGNORECASE
        if item == 'x':
            i |= re.X
        if item == 's':
            i |= re.S
        if item == 'g':
            count = 0

    setattr(sedobject, 'flags', i)
    setattr(sedobject, 'count', count)

def get_message(bot, sedregex, nick, chan, qual=None):
    try:
        for message in bot.chans[chan].getlog(nick):
            try:
                if qual:
                    if re.search(sedregex, message) and re.search(qual, message):
                        return message
                else:
                    if re.search(sedregex, message):
                        return message
            except BaseException:
                pass
    except KeyError:
        pass
    return ""

@Hook("PRIVMSG")
def sed(bot, user, to, targ, msg):
    nick = user['nick']

    s = type('SedObject', tuple(), {})
    
    if not SED_REGEX.match(msg):
        return (user,to,targ,msg)

    groups = SED_REGEX.match(msg).groups()
    populate(s, groups)
    set_flags(s, s.flags)

    if s.target:
        nick = s.target

    if s.qual:
        s.msg = get_message(bot, s.to_replace, nick, to, qual=s.qual)
    else:
        s.msg = get_message(bot, s.to_replace, nick, to)

    if not s.msg:
        return (user,to,targ,msg)

    try:
        new_msg = re.sub(s.to_replace, s.replacement, s.msg, s.count, s.flags)
        bot.privmsg(to, "<%s> %s" % (nick, new_msg))
        return (user,to,targ,msg)
    except BaseException:
        traceback.print_exc()

