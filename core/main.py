"""Main entry point module.

This module provides the main entry point for the DYChatBot application.
"""

import sys
from typing import List, NoReturn, Optional

from utils import config as config_utils
from utils import logger as logger_utils

from core import bot


def main(argv: Optional[List[str]] = None) -> NoReturn:
    """Main entry point for the application.

    Args:
        argv: Command line arguments. If None, uses sys.argv.
    """
    if argv is None:
        argv = sys.argv

    # If there are fewer than 2 arguments, show usage and exit
    if len(argv) < 2:
        print("Usage: python -m core.main <config_path>")
        print("Example: python -m core.main config.json")
        sys.exit(1)
        return

    # If we have 2 or more arguments, process the second one
    if argv[1] in ['-h', '--help']:
        print("DYChatBot - Douyin Chat Automation Bot")
        print("")
        print("Usage: python -m core.main <config_path>")
        print("")
        print("Arguments:")
        print("  config_path    Path to the configuration file")
        print("")
        print("Example: python -m core.main config.json")
        sys.exit(0)
        return

    # Get config path from command line arguments
    config_path = argv[1]

    try:
        # Run the bot with the provided config
        run_bot(config_path)
    except Exception as e:
        print(f"Error running bot: {e}")
        sys.exit(1)
        return


def run_bot(config_path: str) -> None:
    """Run the bot with the given configuration.

    Args:
        config_path: Path to the configuration file.
    """
    # Load configuration
    config = config_utils.load_config(config_path)

    # Set up logger
    logger = logger_utils.setup_logger(
        name="DYChatBot",
        level=config["logging"]["level"],
        log_dir=config["logging"]["log_dir"]
    )

    # Create and run bot - use the module-level Bot alias for test patching
    bot_instance = Bot(config, logger)

    try:
        # Set up the bot
        bot_instance.bot_setup()

        # Run the bot
        bot_instance.bot_run()
    except Exception as e:
        logger.error(f"Bot encountered an error: {e}")
        raise
    finally:
        # Clean up resources regardless of success or failure
        bot_instance.bot_cleanup()


# For test mocking compatibility - expose imports at module level
Bot = bot.Bot
config_utils = config_utils
logger_utils = logger_utils


if __name__ == "__main__":
    main(sys.argv)