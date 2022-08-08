from ast import Pass
import requests
import lxml.html as html
import pandas as pd
import os


PAGES=42  #se debe ingresar el numero de paginas a consultar, mercado libre tiene 42 paginas por consulta y 48 registros por pagina. Lo máximo serian 42.
UBICACION='antioquia' #se debe ingresar la ubicación que se desea consultar.

HOME_URL='https://carros.mercadolibre.com.co/antioquia/#applied_filter_id%3Dstate%26applied_filter_name%3DUbicaci%C3%B3n%26applied_filter_order%3D7%26applied_value_id%3DTUNPUEFOVGFiZWI3%26applied_value_name%3DAntioquia%26applied_value_order%3D1%26applied_value_results%3D7544%26is_custom%3Dfalse' 
#pagina inicial de busuqda es importante entrar a mercado libre, filtrar por la ubicacion y copiar el link de la primera pagina.

#El siguiente bloque de codigo recoge los valores que se desean consultar, estos son sacados directamente del codigo html de mercado libre.

# de la pagina inicial donde se encuentran todos los vehiculos podemos obtener el link de cada uno de los vehiculos.
XPATH_LINK_TO_CARS='//li[@class="ui-search-layout__item"]/div/div/div/a/@href' 

#entrando a la pagina de uno de los vehiculos accedemoas a las especificaciones =['Marca', 'Modelo', 'Año', 'Color', 'Tipo de combustible', 'Puertas', 'Transmisión', 'Motor', 'Tipo de carrocería', 'Kilómetros']['Precio']['Link'] 
SPECS_VALUES='//td[@class="andes-table__column andes-table__column--left ui-pdp-specs__table__column"]/span[@class="andes-table__column--value"]/text()'
PRICE_CARS='//span[@class="andes-money-amount__fraction"]/text()'
INNER_LINK='//link[@rel="canonical"]/@href'
INNER_LOC='//div[@class="ui-seller-info__status-info"][2]/div/p/text()'
INNER_LOC_1='//div[@class="ui-seller-info__status-info"]/div/p/text()'# no todas las paginas tienen dos posiciones acá

def parse_specs(link): # esta función se va a encargar de entrar a cada uno de los links de los vehiculos y extraer la información alli contenida que es de nuestro interés, esta se correra dentro de la sigueinte función.
    try:
        response= requests.get(link) #solicitamos acceso, si es posible entramos a él, decodificamos para ecitar errores de lectura y lo volvemos html.fromstring
        if response.status_code==200:
            specs=response.content.decode('utf-8')
            parsed= html.fromstring(specs)
            try: #en bloque vamos a obtener la información analizada de especificaciones y precios.
                specs_values=parsed.xpath(SPECS_VALUES)
                price=parsed.xpath(PRICE_CARS)
                inner_link=parsed.xpath(INNER_LINK)
                inner_loc=parsed.xpath(INNER_LOC)
                if len(specs_values)==9: # algunas especificaciones no tienen el tipo de carroceria con este if lo remplazamos con NA en caso de que no lo tenga.
                    specs_values.insert(8,'NA')
                else:
                    pass
                if len(inner_loc) ==0:
                    inner_loc=parsed.xpath(INNER_LOC_1)# sino tiene dos posiciones toma la otra opcion
                else:
                    pass
                #se crea un dataframe juntando los precios con los valores de las especificaicones.
                df1=pd.DataFrame([specs_values], columns=['Marca', 'Modelo', 'Año', 'Color', 'Tipo de combustible', 'Puertas', 'Transmisión', 'Motor', 'Tipo de carrocería', 'Kilómetros'])
                df2=pd.DataFrame([price],columns=['Precio'])
                df3=pd.DataFrame([inner_link],columns=['Link'])
                df4=pd.DataFrame([inner_loc],columns=['Ubicación'])
                dft=pd.concat([df1,df2], axis=1)
                dft=pd.concat([dft,df3], axis=1)
                dft=pd.concat([dft,df4], axis=1)
                return dft
            except IndexError:
                return 
        else:
             raise ValueError(f'error:{response.status_code}')
    except ValueError as ve:
        print(ve)


def parse_home(): # esta funcione entra a cada uno se los links de las paginas y ejecuta la funcion anterior.
    count=1
    try:
        for i in range (1,PAGES+1): # este loop recorerá el numero de paginas indicadas al inicio.
            if count == 1: # en este IF dejamos la informacion de la pagina 1
                response= requests.get(HOME_URL)
                if response.status_code==200: # este if es gual al de la función anterior, pero con los datos al interior de cada uno de los links.
                    home=response.content.decode('utf-8')
                    parsed= html.fromstring(home)
                    links_to_carr= parsed.xpath(XPATH_LINK_TO_CARS)
                    dft=pd.DataFrame(columns=['Marca', 'Modelo', 'Año', 'Color', 'Tipo de combustible', 'Puertas', 'Transmisión', 'Motor', 'Tipo de carrocería', 'Kilómetros','Precio','Link','Ubicación'])
                    #se crea un dataframe vacio para empezar a agregar cada uno de los links analizados en la primera pagina.
                    for link in links_to_carr:
                        df1=parse_specs(link)#crea un df por cada link
                        dft=pd.concat([dft,df1])#agrega el dt frame al daframe que contiene todos los datos.
                    
                    dft=dft.reset_index(drop=True)# reiniciamos el indice para poder juntarlo con la informacion de los links y la ubicación.    
                   

                count+=1
                    
            else: # en este ELSE de la pagina 1 en adelante
                pagina=((count-1)*48)+1
                HOME_URL_1=f'https://carros.mercadolibre.com.co/{UBICACION}/_Desde_{pagina}_NoIndex_True' # se hace este nuevo tipo de url porque en mercado libre cambian con las hojas 
                print(HOME_URL_1)
                response= requests.get(HOME_URL_1)# a partir de acá el codigo es exactamente igual al de el if anterior.
                if response.status_code==200:
                    home=response.content.decode('utf-8')
                    parsed= html.fromstring(home)
                    links_to_carr= parsed.xpath(XPATH_LINK_TO_CARS)
                    dft1=pd.DataFrame(columns=['Marca', 'Modelo', 'Año', 'Color', 'Tipo de combustible', 'Puertas', 'Transmisión', 'Motor', 'Tipo de carrocería', 'Kilómetros','Precio','Link','Ubicación'])
                    count_2=0
                    for link in links_to_carr:
                        if count==2: # este if se hace necesario porque necesito guardar los datos de la primera hoja y conservarlos para la siguiente, entonces el primer if solo corre con el count==0
                            if count_2==0:# acá se hace con el fin de hacer este cambio y que no se me reinicie y borre cada vez que cambie de hoja dft2=dft1                     
                                df2=parse_specs(link)
                                dft1=pd.concat([dft1,df2])
                                dft2=dft1
                                count_2+=1
                            else:
                                df2=parse_specs(link)# el daframe guardado se va agregando al anterior.
                                dft2=pd.concat([dft2,df2])  

                        else:
                            df2=parse_specs(link)
                            dft2=pd.concat([dft2,df2])
 

                    dft2=dft2.reset_index(drop=True) 
                   
                    count+=1 # se suma uno al contador para segur las paginas.
                    

        df_total=pd.concat([dft,dft2]).reset_index(drop=True)# se unen los dos dataframes anteriores u se reiniciia el indice.
        os.makedirs('Datos_obtenidos/', exist_ok=True) # si no existe se crea el directorio.
        out_file_name='Datos_obtenidos/'+UBICACION+'.csv'#  se guarda el archivo con el nombre de la ubicación para ser analizado posteriormente.

                                       
        return (df_total.to_csv(out_file_name))        
                                 
    except ValueError as ve:
        print(ve)
    
def run():
    parse_home()

if __name__=='__main__':
    run()