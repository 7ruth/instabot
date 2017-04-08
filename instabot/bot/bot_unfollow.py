from tqdm import tqdm

from . import limits
from . import delay


def unfollow(self, user_id):
    user_id = self.convert_to_user_id(user_id)
    if self.check_user(user_id):
        return True  # whitelisted user
    if limits.check_if_bot_can_unfollow(self):
        delay.unfollow_delay(self)
        if super(self.__class__, self).unfollow(user_id):
            self.User.counters.unfollows += 1
            return True
    else:
        self.logger.info("Out of unfollows for today.")
    return False


def unfollow_users(self, user_ids):
    broken_items = []
    user_ids = self.prefilter_users_to_unfollow(user_ids)
    for user_id in tqdm(user_ids):
        if not self.unfollow(user_id):
            delay.error_delay(self)
            broken_items = user_ids[user_ids.index(user_id):]
            break
    self.logger.info("DONE: Total unfollowed %d users. " %
                     self.User.counters.unfollows)
    return broken_items


def unfollow_non_followers(self):
    self.logger.info("Unfollowing non-followers")
    followings = set(self.get_user_following(self.User.user_id))
    self.logger.info("You follow %d users." % len(followings))
    followers = set(self.get_user_followers(self.User.user_id))
    self.logger.info("You are followed by %d users." % len(followers))
    whitelist = set(map(lambda x: int(x), self.User.whitelist))
    self.logger.info("You have %d users in the whitelist." % len(whitelist))
    to_unfollow = followings - followers - whitelist
    self.logger.info("%d users don't follow you back." % len(to_unfollow))
    self.unfollow_users(list(to_unfollow))


def unfollow_everyone(self):
    your_following = self.get_user_following(self.User.user_id)
    self.unfollow_users(your_following)
