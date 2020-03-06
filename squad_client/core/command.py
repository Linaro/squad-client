class SquadClientCommand:
    command = None
    help_text = None
    klasses = {}

    @staticmethod
    def add_commands(subparser):
        for klass in SquadClientCommand.__subclasses__():
            obj = klass()
            if obj.register(subparser) is None:
                SquadClientCommand.klasses[obj.command] = obj

    @staticmethod
    def process(args):
        return SquadClientCommand.klasses[args.command].run(args)

    def register(self, subparser):
        return subparser.add_parser(self.command, help=self.help_text)

    def run(args):
        raise NotImplementedError
