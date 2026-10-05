import os


# Hook for ansible to set the correct environment variables
def env_settings():
    os.environ["PLACEHOLDER"] = "DUMMY"
