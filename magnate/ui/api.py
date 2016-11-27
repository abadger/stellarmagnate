from abc import ABCMeta, abstractmethod

class UserInterface(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, pubpen):
        """Initialize the UserInterface

        :arg pubpen: A :class:`pubmarine.PubPen` object for communicating
            between the UserInterface and the :class:`magnate.Dispatcher`.
            This can safely be used to communicate between pieces of the user
            interface as well as long as you don't publish on an existing channel.
            The pubpen contains a link to the asyncio event loop that may be
            shared by the UserInterface if it supports it.
        """
        pass

    @abstractmethod
    def run(self):
        """Run the interface

        This runs the magnate program.  Since the entire program is event
        driven, it must start the asyncio event loop and the user interface
        event loop (if different).
        """
        pass
