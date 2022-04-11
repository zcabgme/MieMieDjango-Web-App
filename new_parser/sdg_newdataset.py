import pymongo
import pymysql
import csv
# from main.CONFIG_READER.read import get_details

class SDG_CSV_RESULTS():
    
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
            self.sdg_goals_no_regex = ['SDG 1','SDG 2','SDG 3','SDG 4','SDG 5','SDG 6','SDG 7','SDG 8','SDG 9','SDG 10','SDG 11','SDG 12','SDG 13','SDG 14','SDG 15','SDG 16','SDG 17','Misc']  
            self.sdg_goals = ['.*SDG 1".*','.*SDG 2.*','.*SDG 3.*','.*SDG 4.*','.*SDG 5.*','.*SDG 6.*','.*SDG 7.*','.*SDG 8.*','.*SDG 9.*','.*SDG 10.*','.*SDG 11.*','.*SDG 12.*','.*SDG 13.*','.*SDG 14.*','.*SDG 15.*','.*SDG 16.*','.*SDG 17.*','.*Misc.*']
    def generate_csv_file(self):
        con_mongo = pymongo.MongoClient('mongodb+srv://yzyucl:qq8588903@miemie.jbizr.mongodb.net/myFirstDatabase?retryWrites=true&w=majority')
        con_sql = pymysql.connect(host=self.client, port=self.port, db=self.database, user=self.username, password=self.password)
        cursor = con_sql.cursor(pymysql.cursors.DictCursor)
        db = con_mongo.Scopus
        collection = db.MatchedModules
        with open("sdg_csv_new.csv","w+",encoding='utf-8') as file:
             csv_writer = csv.writer(file)
             csv_writer.writerow(["Faculty","SDG 1","SDG 2","SDG 3","SDG 4","SDG 5","SDG 6","SDG 7","SDG 8","SDG 9","SDG 10","SDG 11","SDG 12","SDG 13","SDG 14","SDG 15","SDG 16","SDG 17","Misc"])
             for a in self.Faculty:
                newlist = []
                for b in range(0,len(self.sdg_goals)):
                #--------------------------------------------------------------
                    sdg_file1 = self.sdg_goals[b]
                    sdg_file = sdg_file1.replace(" ",'')
                    if len(sdg_file) == 8:
                        sdg_file = sdg_file[2:6]
                    elif len(sdg_file) == 9 and sdg_file[6] != "\"":
                        sdg_file = sdg_file[2:7]
                    else:
                        sdg_file = sdg_file[2:6]
                    sdg_list_id = []
                    result = collection.find({"Related_SDG"+"."+self.sdg_goals_no_regex[b]: {'$exists': True}})
                    for i in result:
                        sdg_list_id.append(i["Module_ID"])
                    sdg_list_faculty = []
                    sql = "SELECT * FROM moduledata"
                    # execute SQL
                    cursor.execute(sql)
                    # get SQL data
                    results = cursor.fetchall()
                    for row in results:
                        id = row['Module_ID']
                        faculty = row['Faculty']
                        for i in sdg_list_id:
                            if i == row['Module_ID']:
                                sdg_list_faculty.append(faculty)
                    newlist.append(sdg_list_faculty)
                                   
                    #----------------------------------------------------------------------------
                csv_writer.writerow([a,newlist[0].count(a),newlist[1].count(a),newlist[2].count(a),newlist[3].count(a),newlist[4].count(a),newlist[5].count(a),newlist[6].count(a),newlist[7].count(a),newlist[8].count(a),newlist[9].count(a),newlist[10].count(a),newlist[11].count(a),newlist[12].count(a),newlist[13].count(a),newlist[14].count(a),newlist[15].count(a),newlist[16].count(a),newlist[17].count(a)])
        # close SQL
        con_sql.close()
    def run(self):
        self.generate_csv_file()
        
SDG_CSV_RESULTS2().run()