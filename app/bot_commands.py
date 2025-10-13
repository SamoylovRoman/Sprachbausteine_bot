from aiogram.types import BotCommand

editor_commands = [
    BotCommand(command="start", description="Bot starten"),
    BotCommand(command="add_example", description="Neues Beispiel hinzufügen"),
    BotCommand(command="list_examples", description="Alle Beispiele anzeigen"),
    BotCommand(command="add_access_codes", description="Die Zugangscodes hinzufügen"),
]

user_commands = [
    BotCommand(command="start", description="Bot starten"),
    BotCommand(command="start_training", description="Training starten"),
    BotCommand(command="my_statistics", description="Meine Statistik anzeigen"),
    BotCommand(command="bot_settings", description="Bot-Einstellungen"),
    BotCommand(command="feedback", description="Feedback an Entwickler")
]
