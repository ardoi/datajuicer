from lsjuicer.inout.db.sqlbase import dbmaster
import os


def default_configuration():
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
        if dbmaster.get_config_setting_value(key):
            print "config value: %s=%s" % (key, str(default[key]))
            continue
        else:
            print "setting default config value: %s=%s"\
                % (key, str(default[key]))
            dbmaster.set_config_setting(key, default[key])
