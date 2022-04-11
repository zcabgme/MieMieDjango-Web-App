import pymongo
import pymysql
import csv
# from main.CONFIG_READER.read import get_details

class HA_CSV_RESULTS():
    
    def __init__(self):
            self.client = 'localhost' # change this information to your local database information
            self.database = 'mysqlmiemie'
            self.port = 3306
            self.username = 'root'
            self.password = 'Gomeni73'
           # self.driver = '{MySQL ODBC 8.0 Unicode Driver}'
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
        con_sql = pyodbc.connect('DRIVER=/usr/local/mysql-connector-odbc-8.0.28-macos11-x86-64bit/lib/libmyodbc8a.so;SERVER=127.0.0.1;DATABASE=mysqlmiemie;UID=root;PWD=Gomeni73;')
        cursor = con_sql.cursor()
        db = con_mongo.Scopus
        collection = db.MatchedHAModules
        with open("ha_csv_new.csv","w+",encoding='utf-8') as file:
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
                                ha_list_faculty.append(faculty)
                    newlist.append(ha_list_faculty)
                                   
                    #----------------------------------------------------------------------------
                csv_writer.writerow([a,newlist[0].count(a),newlist[1].count(a),newlist[2].count(a),newlist[3].count(a),newlist[4].count(a),newlist[5].count(a),newlist[6].count(a),newlist[7].count(a),newlist[8].count(a),newlist[9].count(a),newlist[10].count(a),newlist[11].count(a),newlist[12].count(a),newlist[13].count(a),newlist[14].count(a),newlist[15].count(a),newlist[16].count(a),newlist[17].count(a),newlist[18].count(a)])
        # close SQL
        con_sql.close()
    def run(self):
        self.generate_csv_file()
        
HA_CSV_RESULTS().run()