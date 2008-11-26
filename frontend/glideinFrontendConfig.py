import string
import os.path

############################################################
#
# Configuration
#
############################################################

class FrontendConfig:
    def __init__(self):
        # set default values
        # user should modify if needed

        self.frontend_descript_file = "frontend.descript"
        self.group_descript_file = "group.descript"
        self.params_descript_file = "params_const.cfg"
        self.exprs_descript_file = "params_expr.cfg"

# global configuration of the module
frontendConfig=FrontendConfig()


############################################################
#
# Generic Class
# You most probably don't want to use these
#
############################################################

# loads a file composed of
#   NAME VAL
# and creates
#   self.data[NAME]=VAL
# It also defines:
#   self.config_file="name of file"
class ConfigFile:
    def __init__(self,config_dir,config_file,convert_function=repr):
        self.config_dir=config_dir
        self.config_file=config_file
        self.load(os.path.join(config_dir,config_file),convert_function)
        self.derive()

    def load(self,fname,convert_function):
        self.data={}
        fd=open(fname,"r")
        try:
            lines=fd.readlines()
            for line in lines:
                if line[0]=="#":
                    continue # comment
                if len(string.strip(line))==0:
                    continue # empty line
                larr=string.split(line,None,1)
                lname=larr[0]
                if len(larr)==1:
                    lval=""
                else:
                    lval=larr[1][:-1] #strip newline
                exec("self.data['%s']=%s"%(lname,convert_function(lval)))
        finally:
            fd.close()

    def derive(self):
        return # by default, do nothing

# load from the group subdir
class GroupConfigFile(ConfigFile):
    def __init__(self,base_dir,group_name,config_file,convert_function=repr):
        ConfigFile.__init__(self,os.path.join(base_dir,"group_"+group_name),config_file,convert_function)
        self.group_name=group_name

# load both the main and group subdir config file
# and join the results
class JoinConfigFile(ConfigFile):
    def __init__(self,base_dir,group_name,config_file,convert_function=repr):
        ConfigFile.__init__(self,base_dir,config_file,convert_function)
        self.group_name=group_name
        group_obj=GroupConfigFile(base_dir,group_name,config_file,convert_function)
        #merge by overriding whatever is found in the subdir
        for k in group_obj.data.keys():
            self.data[k]=group_obj.data[k]

############################################################
#
# Configuration
#
############################################################

class FrontendDescript(ConfigFile):
    def __init__(self,config_dir):
        global frontendConfig
        ConfigFile.__init__(self,config_dir,frontendConfig.frontend_descript_file,
                            repr) # convert everything in strings
        

class ElementDescript(GroupConfigFile):
    def __init__(self,base_dir,group_name):
        global frontendConfig
        GroupConfigFile.__init__(self,base_dir,group_name,frontendConfig.group_descript_file,
                                 repr) # convert everything in strings

class ParamsDescript(JoinConfigFile):
    def __init__(self,base_dir,group_name):
        global frontendConfig
        JoinConfigFile.__init__(self,base_dir,group_name,frontendConfig.params_descript_file,
                                lambda s:s) # values are in python format

class ExprsDescript(JoinConfigFile):
    def __init__(self,base_dir,group_name):
        global frontendConfig
        JoinConfigFile.__init__(self,base_dir,group_name,frontendConfig.exprs_descript_file,
                                lambda s:s) # values are in python format


############################################################
#
# Merged configuration
#
############################################################

# not everything is merged
# the old element can still be accessed
class ElementMergedDescription:
    def __init__(self,base_dir,group_name):
        self.frontend_data=FrontendDescript(base_dir).data
        if not (group_name in string.split(frontend_data['Groups'],',')):
            raise RuntimeError, "Group '%s' not supported: %s"%(group_name,frontend_data['Groups'])
        
        self.element_data=ElementDescript(base_dir,group_name).data
        self.group_name=group_name

        self.merge()

    #################
    # Private
    def merge(self):
        self.merged_data={}

        for t in ('FactoryCollectors','JobSchedds'):
            self.merged_data[t]=string.split(frontend_data[t],',')+string.split(element_data[t],',')
            if len(self.merged_data[t]):
                raise RuntimeError,"Found empty %s!"%t
        for t in ('FactoryQueryExpr','JobQueryExpr'):
            self.merged_data[t]="(%s) && (%s)"%(frontend_data[t],element_data[t])
        for t in ('FactoryMatchAttrs','JobMatchAttrs'):
            attributes=[]
            names=[]
            for el in eval(frontend_data[t])+eval(element_data[t]):
                el_name=el[0]
                if not (el_name in names):
                    attributes.append(el)
                    names.append(el_name)
            self.merged_data[t]=attributes
        for t in ('MatchExpr',):
            self.merged_data[t]="(%s) and (%s)"%(frontend_data[t],element_data[t])
            self.merged_data[t+'CompiledObj']=compile(self.merged_data[t],"<string>","eval")

        return

        