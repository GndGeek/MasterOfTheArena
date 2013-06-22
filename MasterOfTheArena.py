import praw
from time import sleep

k_subreddit_name = "ArenaForumGame"
k_command_interface_name = u"Automatic Statistics Tracker - Buy Items Here"
k_items = {"fireball": (13, 1), "forcefield": (7, 1), "heal": (10, 1), "blink": (5, 1), "enchancestrength": (11, 1), "energize": (9, 1), "drainlife": (12, 1), "chargeweapon": (8, 1), "frost": (6, 1), "rootsnare": (14, 1), "shiv": (6, 1), "longspear": (7, 1), "broadsword": (5, 1), "club": (9, 1), "throwingaxes": (8, 1), "shortbow": (9, 1), "woodenbuckler": (5, 1), "lightarmor": (7, 1), "arrows": (2, 1), "soldiertraining": (15, 1), "counterspell": (14, 2)}
k_level_thresholds = [0, 20, 60, 140, 250]

def calculate_level(xp):
    for (i, threshold) in enumerate(k_level_thresholds):
        if xp < threshold: return i
    return len(k_level_thresholds)

class UserInfo:
    def __init__(self, xp, gold, items):
        self.xp = xp
        self.gold = gold
        self.items = items
    
    def generate_flair(self):
        return str(self.xp) + "XP " + str(self.gold) + "GP " + " ".join(self.items)

class MasterOfTheArena:
    def __init__(self):
        self.connect_to_interface()
    
    def do_setup(self, user, command, *args):
        print "Setting Up " + user.name
        self.subreddit.set_flair(user, UserInfo(0, 20, []).generate_flair(), "level1")
        return True
    
    def do_purchase(self, user, command, item, *args):
        print "Purchasing " + item + " for " + user.name
        info = self.analyze_flair(user)
        if not info: return "No Info"
        cost, level = k_items[item.lower()]
        if (not level) or (cost > info.gold) or (level > calculate_level(info.xp)):
            return "Cannot Purchase"
        info.items.append(item)
        info.gold -= cost
        self.subreddit.set_flair(user, info.generate_flair(), "level" + str(calculate_level(info.xp)))
    
    def do_sell(self, user, command, item, *args):
        print "Selling " + item + " for " + user.name
        info = self.analyze_flair(user)
        if not info: return "No Info"
        cost, level = k_items[item.lower()]
        if not (level and (item in info.items)):
            return "Item Not Available"
        info.items.remove(item)
        info.gold += cost
        self.subreddit.set_flair(user, info.generate_flair(), "level" + str(calculate_level(info.xp)))
    
    def do_gold(self, user, command, target, quantity, *args):
        if not self.is_mod(user.name): return "Permissions"
        print "Giving " + quantity + "GP to " + target
        info = self.analyze_flair(target)
        if not info: return "No Info"
        try: info.gold += int(quantity)
        except: return "Bad Data"
        self.subreddit.set_flair(user, info.generate_flair(), "level" + str(calculate_level(info.xp)))

    def do_xp(self, user, command, target, quantity, *args):
        if not self.is_mod(user.name): return "Permissions"
        print "Giving " + quantity + "XP to " + target
        info = self.analyze_flair(target)
        if not info: return "No Info"
        try: info.xp += int(quantity)
        except: return "Bad Data"
        self.subreddit.set_flair(user, info.generate_flair(), "level" + str(calculate_level(info.xp)))
    
    def is_mod(self, username):
        return username in [user.name for user in self.client.get_moderators(self.subreddit)]

    def analyze_flair(self, user):
        try:
            flair_string = self.client.get_flair(self.subreddit, user)["flair_text"]
            flair_components = flair_string.split()
            if len(flair_components) < 2: return None
            if not (flair_components[0].endswith("XP") and flair_components[1].endswith("GP")): return None
            xp = int(flair_components[0][:-2])
            gold = int(flair_components[1][:-2])
            items = flair_components[2:]
            return UserInfo(xp, gold, items)
        except:
            return None
    
    def connect_to_interface(self):
        print "Connecting to Reddit..."
        self.client = praw.Reddit(user_agent="/u/GeekOfGeekAndDad's MasterOfTheArena 0.1")
        self.client.login(raw_input("Username: "), raw_input("Password: "))
        print "Connected."
        
        print "Loading Command Interface..."
        self.subreddit = self.client.get_subreddit(k_subreddit_name)
        submissions = self.subreddit.get_new(limit=None)
        self.interface = None
        for sub in submissions:
            if sub.title == k_command_interface_name:
                self.interface = sub
                break
        if not self.interface:
            raise KeyError()
        print "Command Interface Loaded."
    
    def analyze_commands(self):
        print "Analyzing Commands..."
        self.interface.refresh()
        comments = self.interface.comments
        comments.reverse()
        for command in comments:
            command_text = str(command)
            if command_text.startswith("//"):
                split_command = command_text.split()
                split_command[0] = split_command[0][2:]
                command_user = command.author
                command_type = split_command[0].lower()
                if command_type == "purchase" or command_type == "buy":
                    self.do_purchase(command_user, *split_command)
                elif command_type == "setup":
                    self.do_setup(command_user, *split_command)
                elif command_type == "sell" or command_type == "refund":
                    self.do_sell(command_user, *split_command)
                elif command_type == "gold":
                    self.do_gold(command_user, *split_command)
                elif command_type == "xp":
                    self.do_xp(command_user, *split_command)
            command.remove(spam=False)
            command.delete()
        print "Command Analysis Complete."

bot = MasterOfTheArena()
while True:
    bot.analyze_commands()
    sleep(30)