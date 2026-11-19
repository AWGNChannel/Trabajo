import math
from dataclasses import dataclass, fields, field


@dataclass
class Config:

    # Constantes
    h_planck = 6.62607015e-34 #[J*s]
    c0 = 299792458.0  #[m/s]

    # Atributos
    longitud_onda_nm: float = 450.0
    receptor: str = 'PIN'
    potencia_w: float = 0.001
    angulo_deg: float = 0.0
    diezmado: int = 1
    distancia_m: float = 1.0
    intervalo_s: float = 1.0
    a: float = 0.18
    b: float = 0.11
    g: float = 0.924
    max_rayos: int = 100
    max_eventos: int = 10000
    limite_lateral_m: float = 200.0
    semilla: int = 42
    absorcion: str = 'eventos'


    # Methods to Manage the class
    def toString(self) :
        return str(self)

    def toDict(self) :
        cat = self.toString()
        # Format = Config(att1=x1, att2=x2, ..., attn=xn)
        cat = cat.replace('Config(','').replace(')','')
        attributes = cat.split(', ')
        confDict = {}
        for i in range(0,len(attributes)) :
            att_n_value = attributes[i].split('=')
    
            # Add the attribute and the value
            confDict.update(dict({att_n_value[0]: att_n_value[1]}))

        return confDict




class ConfigHandler :
    def __init__(self, configClass, argsList) :
        # argList it's a 'key'-'value' dictionary of each one of the data fields.

        if not argsList == None :
            print("1a@####################\n#################\n##############")
            cfg = classConfigList(configClass, argsList)
        else :
            print("2a@####################\n#################\n##############")
            cfg = configClass
        
        # All exceptions are located in this class, but are handled by the top, Application 
        # Math exceptions
        
        try :
            if cfg.longitud_onda_nm <= 0 or cfg.distancia_m <= 0 or cfg.intervalo_s <= 0:
                raise ValueError('Longitud de onda, distancia e intervalo deben ser positivos.')
            if cfg.potencia_w < 0 or cfg.a < 0 or cfg.b < 0 or not -1 < cfg.g < 1:
                raise ValueError('Potencia, a y b deben ser no negativos y -1 < g < 1.')
            if cfg.diezmado < 1 or cfg.max_rayos < 1 or cfg.max_eventos < 1 or cfg.limite_lateral_m <= 0:
                raise ValueError('diezmado, num_rayos, max_eventos and limite_lateral_m should be exctrictly positives.')
            if not -90 < cfg.angulo_deg < 90:
                raise ValueError('The incident angle should be set in the range -90º and 90º.')
            if cfg.semilla < 0 :
                raise ValueError('semilla is restricted to only positive integer values.')            
        except ValueError as err :
            print(err)


        # Invalid Arguments

        try :
            if not (cfg.absorcion.lower() ==  'eventos' or cfg.absorcion.lower() == 'continua') :
                raise NameError('Propagation should be set in either \'eventos\' or \'continua\'')
            if not (cfg.receptor.upper() ==  'APD' or cfg.receptor.upper() == 'PIN') :
                raise NameError('Receptor should be set in either \'APD\' or \'PIN\'')
        except NameError as err :
            print(err)   


    # Returns the dataclass from a dictionary set with part of the keys (but not all) beeing the fields.
    def classConfigList(className, argsDict) :
        fieldSet = {f.name for f in fields(className) if f.init}
        filteredArgsDict = {k : v for k, v in argsDict.items() if k in fieldSet}
        return className(**filteredArgsDict)

    """
    ######################################
    # Methods used for the other classes #
    ######################################
    """


    # Returns a dictionary of the keys and values of set Parameters, constants, etc
    def returnDatabase(self, className, fieldSetNeeded) :
        if fieldSetNeeded == None : 
            fieldSet = {f.name for f in fields(className) if f.init}
        else :
            fieldSet = fieldSetNeeded

        dbs = {}
        for field in fieldSet :
            if field in fields(className) : 
                dbs.update(dict({field.name: getattr(className, field.Name)}) )

        return dbs 
                
        

class Database() :

    className : Config 
    database_handler : ConfigHandler 

    def __init__(self) :
        # Create a handler to test teh values and work with them

        self.className = Config()
        self.database_handler = ConfigHandler(className, None)

    def returnDatabase(self) :
        
        dbs = self.database_handler.returnDatabase(Config(), None)
        return dbs 
        
         
if __name__ == "__main__" :

    className = Config()
    fieldSet = className.toString()
    print(fieldSet)

    fieldSetDict = className.toDict()
    for key, value in fieldSetDict.items() :
        print(f'Attr : {key} = Value : {value}')

    print("##########################\n########################\n######################")
    fieldSet = {f.name for f in fields(className) if f.init}
    print(fieldSet)
    print("##########################\n########################\n######################")

    classData = Database()
    database = classData.returnDatabase()

    newDataBase = Config(**database)
    fieldSet = newDataBase.toString()
    print(fieldSet)

    """
    db = Database()
    dbs = db.returnDatabase()
    # Print both keys and values
    print("Keys and Values:")
    for key, value in dbs.items():
        print(f"{key}: {value}")
    """