from hashlib import new
import pymongo
import pymysql
import csv
# from main.CONFIG_READER.read import get_details

class HA_CSV_RESULTS2():
    
    def __init__(self):
            self.client = '' # change this information to your local database information
            self.database = ''
            self.port = 3306
            self.username = ''
            self.password = ''
            #self.driver = '{MySQL ODBC 8.0 Unicode Driver}'
            # self.database = get_details("SQL_SERVER", "database")
            # self.username = get_details("SQL_SERVER", "username")
            # self.client = get_details("SQL_SERVER", "client")
            # self.password = get_details("SQL_SERVER", "password")
            # self.port = 3306
            self.Faculty = ['Faculty of Arts and Humanities','Faculty of Social and Historical Sciences','Faculty of Brain Sciences','Faculty of Life Sciences','Faculty of the Built Environment', 'School of Slavonic and Eastern European Studies'
                   ,'Institute of Education', 'Faculty of Engineering Sciences','Faculty of Mathematical and Physical Sciences', 'Faculty of Medical Sciences','Faculty of Population Health Sciences']
            self.ha_goals_no_regex = ['HA 1','HA 2','HA 3','HA 4','HA 5','HA 6','HA 7','HA 8','HA 9','HA 10','HA 11','HA 12','HA 13','HA 14','HA 15','HA 16','HA 17','HA 18','HA 19']  
            self.ha_goals = ['.*HA 1".*','.*HA 2.*','.*HA 3.*','.*HA 4.*','.*HA 5.*','.*HA 6.*','.*HA 7.*','.*HA 8.*','.*HA 9.*','.*HA 10.*','.*HA 11.*','.*HA 12.*','.*HA 13.*','.*HA 14.*','.*HA 15.*','.*HA 16.*','.*HA 17.*','.*HA 18.*','.*HA 19.*']
    def generate_csv_file(self):
        con_mongo = pymongo.MongoClient('mongodb+srv://yzyucl:qq8588903@miemie.jbizr.mongodb.net/myFirstDatabase?retryWrites=true&w=majority')
        con_sql = pymysql.connect(host=self.client, port=self.port, db=self.database, user=self.username, password=self.password)
        cursor = con_sql.cursor(pymysql.cursors.DiclocalhosttCursor)
        db = con_mongo.Scopus
        collection = db.MatchedHAModules
        with open("ha_csv_new2.csv","w+",encoding='utf-8') as file:
             csv_writer = csv.writer(file)
             csv_writer.writerow(["Faculty","HA 1","HA 2","HA 3","HA 4","HA 5","HA 6","HA 7","HA 8","HA 9","HA 10","HA 11","HA 12","HA 13","HA 14","HA 15","HA 16","HA 17","HA 18","HA 19"])
             for a in self.Faculty:
                newlist = []
                for b in range(0,len(self.ha_goals)):
                #--------------------------------------------------------------
                    ha_file1 = self.ha_goals[b]
                    ha_file = ha_file1.replace(" ",'')
                    if len(ha_file) == 8:
                        ha_file = ha_file[2:6]
                    elif len(ha_file) == 9 and ha_file[6] != "\"":
                        ha_file = ha_file[2:7]
                    else:
                        ha_file = ha_file[2:6]
                    ha_list_id = []
                    result = collection.find({"Related_HA"+"."+self.ha_goals_no_regex[b]: {'$exists': True}})
                    for i in result:
                        ha_list_id.append(i["Module_ID"])
                    ha_list_faculty = []
                    ha_list_mod = []
                    sql = "SELECT * FROM moduledata"
                    # execute SQL
                    cursor.execute(sql)
                    # get SQL data
                    results = cursor.fetchall()           
                    for row in results:
                        id = row['Module_ID']
                        faculty = row['Faculty']
                        for i in ha_list_id:
                            if i == row['Module_ID']:
                                res = []
                                res.append(id)
                                res.append(faculty)
                                ha_list_mod.append(res)
                    
                    ha_mod_res = []
                    for j in range( 0, len(ha_list_mod)):
                            if ha_list_mod[j][1] == a:
                                ha_mod_res.append(ha_list_mod[j][0])
                    if ha_mod_res == []:
                        newlist.append("")
                    else:
                        newlist.append(ha_mod_res)
                    
                    #----------------------------------------------------------------------------
                csv_writer.writerow([a,newlist[0],newlist[1],newlist[2],newlist[3],newlist[4],newlist[5],newlist[6],newlist[7],newlist[8],newlist[9],newlist[10],newlist[11],newlist[12],newlist[13],newlist[14],newlist[15],newlist[16],newlist[17],newlist[18]])
        # close SQL
        con_sql.close()
    def run(self):
        self.generate_csv_file()
        
HA_CSV_RESULTS2().run()

