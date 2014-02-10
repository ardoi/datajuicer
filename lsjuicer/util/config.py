from lsjuicer.inout.db.sqlbase import dbmaster
import os


def default_configuration(override = False):
    default = {
        "visualization_options_reference":
        {"blur": 0.3, "colormap": "gist_heat",
         "saturation": 5, 'colormap_reverse': False},
        #
        "ome_folder": os.path.join(os.getenv('HOME'), '.JuicerTemp'),
        #
        "filetype": "oib",
    }
    for key in default:
        val= dbmaster.get_config_setting_value(key)
        if val and not override:
            print "config value: %s=%s" % (key, str(val))
            continue
        else:
            print "setting default config value: %s=%s"\
                % (key, str(default[key]))
            dbmaster.set_config_setting(key, default[key])
