import datetime
import atexit
import signal

from ..api import API
from ..parser import Parser

from .bot_get import get_media_owner, get_your_medias, get_user_medias
from .bot_get import get_timeline_medias, get_hashtag_medias, get_user_info
from .bot_get import get_geotag_medias, get_timeline_users, get_hashtag_users
from .bot_get import get_media_commenters
from .bot_get import get_user_followers, get_user_following, get_media_likers
from .bot_get import get_media_comments, get_geotag_users
from .bot_get import get_comment, get_media_info, get_user_likers

from .bot_like import like, like_medias, like_timeline, like_user, like_users
from .bot_like import like_hashtag, like_geotag, like_followers, like_following

from .bot_unlike import unlike, unlike_medias, unlike_user

from .bot_follow import follow, follow_users, follow_followers, follow_following

from .bot_unfollow import unfollow, unfollow_users, unfollow_non_followers
from .bot_unfollow import unfollow_everyone

from .bot_comment import comment, comment_medias, comment_geotag, comment_users
from .bot_comment import comment_hashtag, is_commented

from .bot_block import block, unblock, block_users, unblock_users, block_bots

from .bot_filter import filter_medias, check_media, filter_users, check_user
from .bot_filter import check_not_bot, prefilter_users_to_follow
from .bot_filter import prefilter_users_to_unfollow, prefilter_users_to_interract

from .bot_support import check_if_file_exists, read_list_from_file
from .bot_support import add_whitelist, add_blacklist

from .bot_stats import save_user_stats


class Bot(API):

    def __init__(self,
                 username=None,
                 password=None,
                 whitelist=False,
                 blacklist=False,
                 comments_file=False,
                 proxy=None):

        super(self.__class__, self).__init__(username=username,
                                             password=password,
                                             proxy=proxy,
                                             std_logger=True)

        apis = API.load_all()
        if apis is None:
            warnings.warn("No users available.")
            return None
        self.logger("Parser Accounts available: %d" % len(apis))
        self.parser = Parser(apis=apis)

        self.User.start_time = datetime.datetime.now()

        if not self.User.bot_is_set:
            self.User.following = []
            self.User.followers = []
            self.User.blacklist = []
            self.User.whitelist = []
            self.User.comments = []
            self.set_counters()
            self.set_limits()
            self.set_filters()
            self.set_delays()
            self.User.bot_is_set = True

        if whitelist:
            self.User.whitelist = read_list_from_file(whitelist)
        if blacklist:
            self.User.blacklist = read_list_from_file(blacklist)

        if comments_file:
            self.User.comments = read_list_from_file(comments_file)
        self.prepare()

    def set_counters(self):
        self.User.counters.likes = 0
        self.User.counters.unlikes = 0
        self.User.counters.follows = 0
        self.User.counters.unfollows = 0
        self.User.counters.blocks = 0
        self.User.counters.unblocks = 0
        self.User.counters.comments = 0

    def set_limits(self,
                   max_likes_per_day=1000,
                   max_unlikes_per_day=1000,
                   max_follows_per_day=350,
                   max_unfollows_per_day=350,
                   max_comments_per_day=100,
                   max_blocks_per_day=100,
                   max_unblocks_per_day=100):
        self.User.limits.max_likes_per_day = max_likes_per_day
        self.User.limits.max_unlikes_per_day = max_unlikes_per_day
        self.User.limits.max_follows_per_day = max_follows_per_day
        self.User.limits.max_unfollows_per_day = max_unfollows_per_day
        self.User.limits.max_comments_per_day = max_comments_per_day
        self.User.limits.max_blocks_per_day = max_blocks_per_day
        self.User.limits.max_unblocks_per_day = max_unblocks_per_day

    def set_filters(self,
                    filter_users=True,
                    max_likes_to_like=100,
                    max_followers_to_follow=2000,
                    min_followers_to_follow=10,
                    max_following_to_follow=2000,
                    min_following_to_follow=10,
                    max_followers_to_following_ratio=10,
                    max_following_to_followers_ratio=2,
                    min_media_count_to_follow=3,
                    max_following_to_block=2000,
                    stop_words=None):
        if stop_words is None:
            stop_words = ['shop', 'store', 'free']
        self.User.filters.filter_users = filter_users
        self.User.filters.max_likes_to_like = max_likes_to_like
        self.User.filters.max_followers_to_follow = max_followers_to_follow
        self.User.filters.min_followers_to_follow = min_followers_to_follow
        self.User.filters.max_following_to_follow = max_following_to_follow
        self.User.filters.min_following_to_follow = min_following_to_follow
        self.User.filters.max_followers_to_following_ratio = max_followers_to_following_ratio
        self.User.filters.max_following_to_followers_ratio = max_following_to_followers_ratio
        self.User.filters.min_media_count_to_follow = min_media_count_to_follow
        self.User.filters.stop_words = stop_words
        self.User.filters.max_following_to_block = max_following_to_block

    def set_delays(self,
                   like_delay=10,
                   unlike_delay=10,
                   follow_delay=30,
                   unfollow_delay=30,
                   comment_delay=60,
                   block_delay=30,
                   unblock_delay=30):
        self.User.delays.like = like_delay
        self.User.delays.unlike = unlike_delay
        self.User.delays.follow = follow_delay
        self.User.delays.unfollow = unfollow_delay
        self.User.delays.comment = comment_delay
        self.User.delays.block = block_delay
        self.User.delays.unblock = unblock_delay

    def version(self):
        from pip._vendor import pkg_resources
        return next((p.version for p in pkg_resources.working_set if p.project_name.lower() == 'instabot'), "No match")

    def logout(self):
        super(self.__class__, self).logout()
        self.logger.info("Bot stopped. "
                         "Worked: %s" % (datetime.datetime.now() - self.start_time))
        self.print_counters()

    def prepare(self):
        if self.User.following == []:
            self.User.following = list(self.get_user_following(self.User.user_id))
        self.User.whitelist = list(
            filter(None, map(self.convert_to_user_id, self.User.whitelist)))
        self.User.blacklist = list(
            filter(None, map(self.convert_to_user_id, self.User.blacklist)))
        self.User.save()
        signal.signal(signal.SIGTERM, self.logout)
        atexit.register(self.logout)

    def print_counters(self):
        print(self.User.counters)

    # getters

    def get_your_medias(self):
        return get_your_medias(self)

    def get_timeline_medias(self):
        return get_timeline_medias(self)

    def get_user_medias(self, user_id, filtration=True):
        return get_user_medias(self, user_id, filtration)

    def get_hashtag_medias(self, hashtag, filtration=True):
        return get_hashtag_medias(self, hashtag, filtration)

    def get_geotag_medias(self, geotag, filtration=True):
        return get_geotag_medias(self, geotag, filtration)

    def get_media_info(self, media_id):
        return get_media_info(self, media_id)

    def get_timeline_users(self):
        return get_timeline_users(self)

    def get_hashtag_users(self, hashtag):
        return get_hashtag_users(self, hashtag)

    def get_geotag_users(self, geotag):
        return get_geotag_users(self, geotag)

    def get_user_info(self, user_id):
        return get_user_info(self, user_id)

    def get_user_followers(self, user_id):
        return get_user_followers(self, user_id)

    def get_user_following(self, user_id):
        return get_user_following(self, user_id)

    def get_media_likers(self, media_id):
        return get_media_likers(self, media_id)

    def get_media_comments(self, media_id):
        return get_media_comments(self, media_id)

    def get_comment(self):
        return get_comment(self)

    def get_media_commenters(self, media_id):
        return get_media_commenters(self, media_id)

    def get_media_owner(self, media):
        return get_media_owner(self, media)

    def get_user_likers(self, user_id, media_count=10):
        return get_user_likers(self, user_id, media_count)

    # like

    def like(self, media_id):
        return like(self, media_id)

    def like_medias(self, media_ids):
        return like_medias(self, media_ids)

    def like_timeline(self, amount=None):
        return like_timeline(self, amount)

    def like_user(self, user_id, amount=None):
        return like_user(self, user_id, amount)

    def like_hashtag(self, hashtag, amount=None):
        return like_hashtag(self, hashtag, amount)

    def like_geotag(self, geotag, amount=None):
        return like_geotag(self, geotag, amount)

    def like_users(self, user_ids, nlikes=None):
        return like_users(self, user_ids, nlikes)

    def like_followers(self, user_id, nlikes=None):
        return like_followers(self, user_id, nlikes)

    def like_following(self, user_id, nlikes=None):
        return like_following(self, user_id, nlikes)

    # unlike

    def unlike(self, media_id):
        return unlike(self, media_id)

    def unlike_medias(self, media_ids):
        return unlike_medias(self, media_ids)

    def unlike_user(self, user):
        return unlike_user(self, user)

    # follow

    def follow(self, user_id):
        return follow(self, user_id)

    def follow_users(self, user_ids):
        return follow_users(self, user_ids)

    def follow_followers(self, user_id):
        return follow_followers(self, user_id)

    def follow_following(self, user_id):
        return follow_following(self, user_id)

    # unfollow

    def unfollow(self, user_id):
        return unfollow(self, user_id)

    def unfollow_users(self, user_ids):
        return unfollow_users(self, user_ids)

    def unfollow_non_followers(self):
        return unfollow_non_followers(self)

    def unfollow_everyone(self):
        return unfollow_everyone(self)

    # comment

    def comment(self, media_id, comment_text):
        return comment(self, media_id, comment_text)

    def comment_hashtag(self, hashtag):
        return comment_hashtag(self, hashtag)

    def comment_medias(self, medias):
        return comment_medias(self, medias)

    def comment_users(self, user_ids):
        return comment_users(self, user_ids)

    def comment_geotag(self, geotag):
        return comment_geotag(self, geotag)

    def is_commented(self, media_id):
        return is_commented(self, media_id)

    # block

    def block(self, user_id):
        return block(self, user_id)

    def unblock(self, user_id):
        return unblock(self, user_id)

    def block_users(self, user_ids):
        return block_users(self, user_ids)

    def unblock_users(self, user_ids):
        return unblock_users(self, user_ids)

    def block_bots(self):
        return block_bots(self)

    # filter

    def prefilter_users_to_follow(self, user_ids):
        return prefilter_users_to_follow(self, user_ids)

    def prefilter_users_to_unfollow(self, user_ids):
        return prefilter_users_to_unfollow(self, user_ids)

    def prefilter_users_to_interract(self, user_ids):
        return prefilter_users_to_interract(self, user_ids)

    def filter_medias(self, media_items, filtration=True):
        return filter_medias(self, media_items, filtration)

    def check_media(self, media):
        return check_media(self, media)

    def check_user(self, user, filter_closed_acc=False):
        return check_user(self, user, filter_closed_acc)

    def check_not_bot(self, user):
        return check_not_bot(self, user)

    def filter_users(self, user_id_list):
        return filter_users(self, user_id_list)

    # support

    def check_if_file_exists(self, file_path):
        return check_if_file_exists(file_path)

    def read_list_from_file(self, file_path):
        return read_list_from_file(file_path)

    def add_whitelist(self, file_path):
        return add_whitelist(self, file_path)

    def add_blacklist(self, file_path):
        return add_blacklist(self, file_path)

    # stats

    def save_user_stats(self, username):
        return save_user_stats(self, username)
