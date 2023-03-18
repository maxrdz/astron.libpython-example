from astron.object_repository import DistributedObject
from datetime import datetime
from globals import *

avatar_speed = 3.0
avatar_rotation_speed = 90.0
__PANDA_RUNNING__ = False

try:  # If base built-in is defined (running on client), import Panda classes
    if base:
        __PANDA_RUNNING__ = True
        from direct.task.Task import Task
except NameError:
    pass  # we're a service


# -------------------------------------------------------------------
# Root
# * Is a container for top-level objects, especially the world and
#   services.
# -------------------------------------------------------------------

class Root(DistributedObject):
    def init(self):
        print("Root.init() for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))


class RootAI(DistributedObject):
    def init(self):
        print("RootAI.init() for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))


class RootAE(DistributedObject):
    def init(self):
        print("RootAE.init() for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))


# -------------------------------------------------------------------
# PointOfContact
# * Is the only DOG, and is the only distobj that a player can
#   contact before logging in.
# * Has interest in LoginServices
# * Redirects player logins to a LoginService, if possible.
# -------------------------------------------------------------------

class AnonymousContact(DistributedObject):
    def init(self):
        print("AnonymousContact.init() for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))

    def login(self, username, password):
        print("Client logging in")
        self.send_update("login", username, password)


class AnonymousContactUD(DistributedObject):
    def init(self):
        print("AnonymousContactUD.init() for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))
        self.login_manager = None
        self.add_ai_interest(RootID, LOGIN_ZONE)

    def login(self, sender, username, password):
        print("Received login request for %d" % (sender, ))
        if self.login_manager:
            self.login_manager.login(sender, username, password)
        else:
            # The login manager AI has not been created yet, so we cannot authenticate!
            self.send_CLIENTAGENT_EJECT(sender, 999, "Server isn't ready for authentication.")
            print("Dropping anonymous client due to missing LoginManager!")

    def interest_distobj_enter(self, view, do_id, parent_id, zone_id):
        if do_id == LoginManagerId:
            print("AnonymousContactUD learned of new LoginManager %d" % (do_id,))
            self.login_manager = view


# -------------------------------------------------------------------
# LoginManager
# * Registers a DistributedWorld
# * Authenticates Clients
# * Makes DistributedWorld create an avatar for new Clients.
# -------------------------------------------------------------------

class LoginManager(DistributedObject):  # Not used in client
    def init(self):
        print(datetime.now().strftime("%H:%M:%S") + " LoginManager.init() for " + str(self.do_id))


class LoginManagerAE(DistributedObject):
    def init(self):
        print(datetime.now().strftime("%H:%M:%S") + " LoginManagerAE.init() for " + str(self.do_id))
        self.add_ai_interest(RootID, WORLD_ZONE)

    def login(self, client_channel, username, password):
        print(datetime.now().strftime("%H:%M:%S") +
              " LoginManagerUD.login(" + username + ", <password>)  in " +
              str(self.do_id) + " for client " + str(client_channel))

        if (username == "guest") and (password == "guest"):
            # Authenticate a client
            # "2" is the magic number for CLIENT_STATE_ESTABLISHED,
            # for which currently no mapping exists.
            self.repo.send_CLIENTAGENT_SET_STATE(client_channel, 2, sender=self.do_id)

            # The client is now authenticated; create an Avatar
            self.world_view.create_avatar(client_channel)
            print("Login successful (user: %s)" % (username,))

        else:
            # Disconnect for bad auth
            # "122" is the magic number for login problems.
            # See https://github.com/Astron/Astron/blob/master/doc/protocol/10-client.md
            self.send_CLIENTAGENT_EJECT(client_channel, 122, "Bad credentials")
            print("Ejecting client for bad credentials (user: %s)", username)

    def interest_distobj_ai_enter(self, view, do_id, parent_id, zone_id):
        if do_id == DistributedWorldId:
            print("LoginManagerAE learned of new World %d" % do_id)
            self.world_view = view


class LoginManagerAI(DistributedObject):
    def init(self):
        print("LoginManagerAI.init() for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))

    def login(self, username, password):
        print(datetime.now().strftime("%H:%M:%S") +
              " LoginManagerAE.login(" + username + ", <password>) in " + str(self.do_id))
        self.send_update("login", username, password)


# -------------------------------------------------------------------
# DistributedWorld
# * has all avatars in its zone 0
# * generates new avatars
# -------------------------------------------------------------------

# class DistributedWorld(DistributedObject):
#    def init(self):
#        print(datetime.now().strftime("%H:%M:%S")+" DistributedWorld.init() for " + str(self.do_id))

# class DistributedWorldOV(DistributedObjectOV):
#    def init(self):
#        print(datetime.now().strftime("%H:%M:%S")+" DistributedWorldOV.init() for " + str(self.do_id))

class DistributedWorld(DistributedObject):
    def init(self):
        print("DistributedWorld.init() for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))


class DistributedWorldAE(DistributedObject):
    def init(self):
        print("DistributedWorldAE.init() for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))

    def create_avatar(self, client_id):
        self.send_update('create_avatar', client_id)


class DistributedWorldAI(DistributedObject):
    def init(self):
        print("DistributedWorldAI.init() for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))

    def create_avatar(self, client_id):
        print(datetime.now().strftime("%H:%M:%S") +
              " DistributedWorldAI.create_avatar(" + str(client_id) + ") in " + str(self.do_id))
        # Create the avatar
        avatar_doid = 1562640  # FIXME: Generate actual random channel for new do_id
        self.repo.create_distobj('DistributedAvatar', avatar_doid, self.do_id, 0)
        # Set the client to be interested in our zone 0. He can't do
        # that himself (or rather: shouldn't be allowed to) as he has
        # no visibility of this object.
        # We're always using the interest_id 0 because different
        # clients use different ID spaces, so why make things more
        # complicated?
        self.repo.send_CLIENTAGENT_ADD_INTEREST(client_id, 0, 0, 0)
        # Set its owner to the client, upon which in the Clients repo
        # magically OV (OwnerView) is generated.
        self.repo.send_STATESERVER_OBJECT_SET_OWNER(avatar_doid, client_id)
        # Declare this to be a session object.
        self.repo.send_CLIENTAGENT_ADD_SESSION_OBJECT(self.do_id, client_id)


"""
class DistributedWorldUD(DistributedObject):
    def init(self):
        print(datetime.now().strftime("%H:%M:%S") + " DistributedWorldUD.init() for " + str(self.do_id))

    def create_avatar(self, client_id):
        print(datetime.now().strftime("%H:%M:%S") +
              " DistributedWorldUD.create_avatar(" + str(client_id) + ") in " + str(self.do_id))
        self.send_update("create_avatar", client_id)
"""


# -------------------------------------------------------------------
# DistributedAvatar
# * represents players in the scene graph
# * routes indications of movement intents to AI
# * updates the actual position and orientation
# -------------------------------------------------------------------

class DistributedAvatar(DistributedObject):
    def init(self):
        print("DistributedAvatar.init() for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))
        if __PANDA_RUNNING__:
            self.model = base.loader.loadModel("./resources/smiley.egg")
            self.model.reparent_to(self)
            self.model.set_h(180.0)
            # Signal local client that this is its avatar
            base.messenger.send("distributed_avatar", [self])

    def delete(self):
        print(datetime.now().strftime("%H:%M:%S") + " DistributedAvatar.delete() for " + str(self.do_id))

    def set_xyzh(self, x, y, z, h):
        if __PANDA_RUNNING__:
            self.model.set_xyzh(x, y, z, h)


class DistributedAvatarOV(DistributedObject):
    def init(self):
        print("DistributedAvatarOV.init() for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))
        if __PANDA_RUNNING__:
            self.model = base.loader.loadModel("./resources/smiley.egg")
            self.model.reparent_to(base.render)
            self.model.set_h(180.0)
            # Signal to client that its received its avatar OV
            base.messenger.send("avatar", [self])

    def delete(self):
        print(datetime.now().strftime("%H:%M:%S") + " DistributedAvatarOV.delete() for " + str(self.do_id))

    def indicate_intent(self, heading, speed):
        self.send_update("indicate_intent", heading, speed)

    def set_xyzh(self, x, y, z, h):
        if __PANDA_RUNNING__:
            self.model.set_xyzh(x, y, z, h)


class DistributedAvatarAE(DistributedObject):
    def init(self):
        print("DistributedAvatarAE.init() for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))


class DistributedAvatarAI(DistributedObject):
    def init(self):
        print("DistributedAvatarAI.init() for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))
        self.heading = 0.0
        self.speed = 0.0

        if __PANDA_RUNNING__:
            self.update_task = base.taskMgr.add(self.update_position, "Avatar position update")

    def delete(self):
        print(datetime.now().strftime("%H:%M:%S") + " DistributedAvatarAI.delete() for " + str(self.do_id))
        if __PANDA_RUNNING__:
            base.taskMgr.remove(self.update_task)

    def indicate_intent(self, heading, speed):
        if (heading < -1.0) or (heading > 1.0) or (speed < -1.0) or (speed > 1.0):
            # Client is cheating!
            # TODO: Eject client
            return
        self.heading = heading
        self.speed = speed

    def update_position(self):
        """
        We don't have to check if we're running Panda here, because
        this function is only used as a callback when set as a task @ init.
        """
        if (self.heading != 0.0) or (self.speed != 0.0):
            dt = base.clock.get_dt()
            self.model.set_h((self.model.get_h() + self.heading * avatar_rotation_speed * dt) % 360.0)
            self.model.set_y(self, self.speed * avatar_speed * dt)
            if self.model.get_x() < -10.0:
                self.model.set_x(-10.0)
            if self.model.get_x() > 10.0:
                self.model.set_x(10.0)
            if self.model.get_y() < -10.0:
                self.model.set_y(-10.0)
            if self.model.get_y() > 10.0:
                self.model.set_y(10.0)
            self.model.set_xyzh(self.model.get_x(), self.model.get_y(), self.model.get_z(), self.model.get_h())
            self.send_update('set_xyzh', self.x, self.y, self.z, self.h)
        return Task.cont
