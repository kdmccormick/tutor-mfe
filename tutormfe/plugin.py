from glob import glob
import os
import pkg_resources

from tutor import hooks as tutor_hooks

from .__about__ import __version__


config = {
    "defaults": {
        "VERSION": __version__,
        "DOCKER_IMAGE": "{{ DOCKER_REGISTRY }}overhangio/openedx-mfe:{{ MFE_VERSION }}",
        "HOST": "apps.{{ LMS_HOST }}",
        "COMMON_VERSION": "{{ OPENEDX_COMMON_VERSION }}",
        "CADDY_DOCKER_IMAGE": "{{ DOCKER_IMAGE_CADDY }}",
        "ENABLE_DYNAMIC_CONFIG": True,
        "ENV_COMMON": {
            "production": {
                "NODE_ENV": "production",
                "ACCESS_TOKEN_COOKIE_NAME": "edx-jwt-cookie-header-payload",
                "BASE_URL": "{{ MFE_HOST }}",
                "CSRF_TOKEN_API_PATH": "/csrf/api/v1/token",
                "CREDENTIALS_BASE_URL": "",
                "DISCOVERY_API_BASE_URL": "{% if DISCOVERY_HOST is defined %}{% if ENABLE_HTTPS %}https{% else %}http{% endif %}://{{ DISCOVERY_HOST }}{% endif %}",
                "ECOMMERCE_BASE_URL": "",
                "ENABLE_NEW_RELIC": "false",
                "FAVICON_URL": "{% if ENABLE_HTTPS %}https{% else %}http{% endif %}://{{ LMS_HOST }}/favicon.ico",
                "LANGUAGE_PREFERENCE_COOKIE_NAME": "openedx-language-preference",
                "LMS_BASE_URL": "{% if ENABLE_HTTPS %}https{% else %}http{% endif %}://{{ LMS_HOST }}",
                "LOGIN_URL": "{% if ENABLE_HTTPS %}https{% else %}http{% endif %}://{{ LMS_HOST }}/login",
                "LOGO_URL": "{% if ENABLE_HTTPS %}https{% else %}http{% endif %}://{{ LMS_HOST }}/theming/asset/images/logo.png",
                "LOGO_TRADEMARK_URL": "{% if ENABLE_HTTPS %}https{% else %}http{% endif %}://{{ LMS_HOST }}/theming/asset/images/logo.png",
                "LOGO_WHITE_URL": "",
                "LOGOUT_URL": "{% if ENABLE_HTTPS %}https{% else %}http{% endif %}://{{ LMS_HOST }}/logout",
                "MARKETING_SITE_BASE_URL": "{% if ENABLE_HTTPS %}https{% else %}http{% endif %}://{{ LMS_HOST }}",
                "PUBLISHER_BASE_URL": "",
                "REFRESH_ACCESS_TOKEN_ENDPOINT": "{% if ENABLE_HTTPS %}https{% else %}http{% endif %}://{{ LMS_HOST }}/login_refresh",
                "SEGMENT_KEY": "",
                "SITE_NAME": "{{ PLATFORM_NAME|replace(\"'\", \"'\\''\")|replace(\" \", \"\\ \") }}",
                "STUDIO_BASE_URL": "{% if ENABLE_HTTPS %}https{% else %}http{% endif %}://{{ CMS_HOST }}",
                "USER_INFO_COOKIE_NAME": "user-info",
            },
            "development": {
                "NODE_ENV": "development",
                "DISCOVERY_API_BASE_URL": "{% if DISCOVERY_HOST is defined %}http://{{ DISCOVERY_HOST }}:8381{% endif %}",
                "LMS_BASE_URL": "http://{{ LMS_HOST }}:8000",
                "LOGIN_URL": "http://{{ LMS_HOST }}:8000/login",
                "LOGO_URL": "http://{{ LMS_HOST }}:8000/theming/asset/images/logo.png",
                "LOGO_TRADEMARK_URL": "http://{{ LMS_HOST }}:8000/theming/asset/images/logo.png",
                "LOGOUT_URL": "http://{{ LMS_HOST }}:8000/logout",
                "MARKETING_SITE_BASE_URL": "http://{{ LMS_HOST }}:8000",
                "REFRESH_ACCESS_TOKEN_ENDPOINT": "http://{{ LMS_HOST }}:8000/login_refresh",
                "STUDIO_BASE_URL": "http://{{ CMS_HOST }}:8001",
            },
        },
        "ACCOUNT_MFE_APP": {
            "name": "account",
            "repository": "https://github.com/edx/frontend-app-account",
            "port": 1997,
            "env": {
                "production": {
                    "COACHING_ENABLED": "",
                    "ENABLE_DEMOGRAPHICS_COLLECTION": "",
                },
            },
        },
        "GRADEBOOK_MFE_APP": {
            "name": "gradebook",
            "repository": "https://github.com/edx/frontend-app-gradebook",
            "port": 1994,
        },
        "LEARNING_MFE_APP": {
            "name": "learning",
            "repository": "https://github.com/edx/frontend-app-learning",
            "port": 2000,
        },
        "PROFILE_MFE_APP": {
            "name": "profile",
            "repository": "https://github.com/edx/frontend-app-profile",
            "port": 1995,
             "env": {
                "production": {
                    "ENABLE_LEARNER_RECORD_MFE": "true",
                },
            },
        },
    },
}

tutor_hooks.Filters.COMMANDS_INIT.add_item(
    (
        "lms",
        ("mfe", "tasks", "lms", "init"),
    )
)
tutor_hooks.Filters.IMAGES_BUILD.add_item(
    (
        "mfe",
        ("plugins", "mfe", "build", "mfe"),
        "{{ MFE_DOCKER_IMAGE }}",
        (),
    )
)


@tutor_hooks.Filters.COMPOSE_MOUNTS.add()
def _mount_frontend_apps(volumes, name):
    """
    If the user mounts any repo named frontend-app-APPNAME, then make sure
    it's available in the APPNAME service container. This is only applicable
    in dev mode, because in production, all MFEs are built and hosted on the
    singular 'mfe' service container.
    """
    prefix = "frontend-app-"
    if name.startswith(prefix):
        # Assumption:
        # For each repo named frontend-app-APPNAME, there is an associated
        # docker-compose service named APPNAME. If this assumption is broken,
        # then Tutor will try to mount the repo in a service that doesn't exist.
        app_name = name.split(prefix)[1]
        volumes += [(app_name, "/openedx/app")]
    return volumes


@tutor_hooks.Filters.IMAGES_PULL.add()
@tutor_hooks.Filters.IMAGES_PUSH.add()
def _add_remote_mfe_image_iff_customized(images, user_config):
    """
    Register MFE image for pushing & pulling if and only if it has
    been set to something other than the default.

    This is work-around to an upstream issue with MFE config. Briefly:
    User config is baked into MFE builds, so Tutor cannot host a generic
    pre-built MFE image. Howevever, individual Tutor users may want/need to
    build and host their own MFE image. So, as a compromise, we tell Tutor
    to push/pull the MFE image if the user has customized it to anything
    other than the default image URL.
    """
    image_tag = user_config["MFE_DOCKER_IMAGE"]
    if not image_tag.startswith("docker.io/overhangio/openedx-mfe:"):
        # Image has been customized. Add to list for pulling/pushing.
        images.append(("mfe", image_tag))
    return images

####### Boilerplate code
# Add the "templates" folder as a template root
tutor_hooks.Filters.ENV_TEMPLATE_ROOTS.add_item(
    pkg_resources.resource_filename("tutormfe", "templates")
)
# Render the "build" and "apps" folders
tutor_hooks.Filters.ENV_TEMPLATE_TARGETS.add_items(
    [
        ("mfe/build", "plugins"),
        ("mfe/apps", "plugins"),
    ],
)
# Load patches from files
for path in glob(
    os.path.join(
        pkg_resources.resource_filename("tutormfe", "patches"),
        "*",
    )
):
    with open(path, encoding="utf-8") as patch_file:
        tutor_hooks.Filters.ENV_PATCHES.add_item((os.path.basename(path), patch_file.read()))

# Add configuration entries
tutor_hooks.Filters.CONFIG_DEFAULTS.add_items(
    [(f"MFE_{key}", value) for key, value in config.get("defaults", {}).items()]
)
tutor_hooks.Filters.CONFIG_UNIQUE.add_items(
    [(f"MFE_{key}", value) for key, value in config.get("unique", {}).items()]
)
tutor_hooks.Filters.CONFIG_OVERRIDES.add_items(list(config.get("overrides", {}).items()))
