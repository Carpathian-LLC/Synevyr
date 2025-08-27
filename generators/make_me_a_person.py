# ------------------------------------------------------------------------------------
# Developed by Carpathian, LLC.
# ------------------------------------------------------------------------------------
# Legal Notice: 
# Distribution Not Authorized
# ------------------------------------------------------------------------------------
# DISCLAIMER:
# This program is for research purposes only. All of the information generated is random and any 
# resemblance to real persons, living or dead, is purely coincidental.

#---------------------------------------------------------------------------------------

__version__ = "BETA - 1.1"

#--------------------------------------IMPORTS------------------------------------------

import random
from datetime import datetime
from generators.location_repo import locations

#--------------------------------------VARIABLES------------------------------------------

email_domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "ymail.com", "comcast.net", "windstream.com", "aol.com", "icloud.com", "mail.com", "protonmail.com", "zoho.com", "gmx.com", "earthlink.net", "cox.net", "verizon.net", "sbcglobal.net", "att.net", "rocketmail.com", "roadrunner.com", "juno.com", "optonline.net", "charter.net", "netzero.net", "frontier.com", "suddenlink.net", "centurylink.net", "cableone.net" ]
male_first_names = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Charles", "Thomas", "Daniel", "Matthew", "Anthony", "Donald", "Paul", "Mark", "Steven", "Andrew", "Kenneth", "Joshua", "Kevin", "Brian", "George", "Edward", "Ronald", "Timothy", "Jason", "Jeffrey", "Ryan", "Jacob", "Gary", "Nicholas", "Eric", "Stephen", "Jonathan", "Larry", "Justin", "Scott", "Brandon", "Benjamin", "Samuel", "Gregory", "Frank", "Alexander", "Raymond", "Patrick", "Jack", "Dennis", "Jerry", "Tyler", "Aaron", "Jose", "Adam", "Henry", "Nathan", "Douglas", "Zachary", "Peter", "Kyle", "Walter", "Harold", "Jeremy", "Ethan", "Carl", "Keith", "Roger", "Gerald", "Terry", "Albert", "Joe", "Arthur", "Willie", "Billy", "Bryan", "Bruce", "Sean", "Roy", "Louis", "Jesse", "Jordan", "Dylan", "Alan", "Ralph", "Gabriel", "Juan", "Wayne", "Eugene", "Logan", "Randy", "Vincent", "Russell", "Elijah", "Phillip", "Bobby", "Johnny", "Caleb", "Mason", "Martin", "Theodore", "Gavin", "Chase", "Edwin", "Barry", "Landon", "Curtis", "Marvin", "Lloyd", "Ricky", "Liam", "Shane", "Brent", "Orlando", "Stanley", "Luther", "Maxwell", "Darren", "Franklin", "Miguel", "Bradley", "Marcus", "Clifford", "Oliver", "Adrian", "Isaac", "Wallace", "Floyd", "Jared", "Alfred", "Herbert", "Ray", "Terrance", "Clarence", "Leroy", "Frederick", "Evan", "Travis", "Troy", "Maurice", "Casey", "Jerome", "Julian", "Leo", "Manuel", "Neil", "Norman", "Ramon", "Sam", "Cory", "Pedro", "Lance", "Elmer", "Aaron", "Brett", "Fernando", "Tony", "Riley", "Elliot", "Diego", "Kurt", "Alex", "Reginald", "Byron", "Lorenzo", "Derek", "Royce", "Garrett", "Danny", "Roland", "Hector", "Eddie", "Frankie", "Alvin", "Glen", "Duane", "Rodney", "Arturo", "Cesar", "Alfonso", "Salvador", "Alfredo", "Spencer", "Graham", "Seth", "Preston", "Damon", "Noel", "Lyle", "Perry", "Alec", "Sylvester", "Dwayne", "Hugo", "Stuart", "Darrell", "Bryant", "Dwight", "Brock", "Jeremiah", "Wesley", "Armando", "Glenn", "Kendall", "Jarrod", "Enrique", "Ernest", "Rafael"]
female_first_names = ["Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen", "Nancy", "Lisa", "Margaret", "Betty", "Dorothy", "Sandra", "Ashley", "Kimberly", "Donna", "Emily", "Michelle", "Carol", "Amanda", "Melissa", "Deborah", "Stephanie", "Rebecca", "Sharon", "Laura", "Cynthia", "Kathleen", "Amy", "Shirley", "Angela", "Helen", "Anna", "Brenda", "Pamela", "Nicole", "Ruth", "Katherine", "Samantha", "Christine", "Emma", "Catherine", "Debra", "Virginia", "Rachel", "Carolyn", "Janet", "Maria", "Heather", "Diane", "Julie", "Joyce", "Victoria", "Jean", "Teresa", "Gloria", "Beverly", "Ruby", "Denise", "Marilyn", "Amber", "Jane", "Doris", "Madison", "Martha", "Diana", "Andrea", "Kelly", "Jacqueline", "Christina", "Frances", "Evelyn", "Joan", "Eileen", "Ruth", "Veronica", "Judy", "Kathy", "Louise", "Grace", "Ann", "Joanne", "Dana", "Hannah", "Paula", "Marie", "Isabel", "Melanie", "Pauline", "Tiffany", "Deanna", "Lauren", "Lori", "Tina", "Wanda", "Cassandra", "Alice", "Jaclyn", "Erin", "Leah", "Suzanne", "Rosa", "Connie", "Sheila", "Dianne", "Megan", "Audrey", "Yvonne", "Jill", "Sally", "Roberta", "Tammy", "Stacy", "Caroline", "Edith", "Claire", "Gwendolyn", "Ella", "Patsy", "Nina", "Maureen", "Renee", "Kristen", "Irene", "Vicki", "Lydia", "Valerie", "Emily", "Michele", "Carmen", "Kristina", "Brittany", "Rita", "Bernice", "Emma", "Bessie", "Lois", "Allison", "Phyllis", "Edna", "Mildred", "Hazel", "Darlene", "Lorraine", "Katie", "Holly", "Veronica", "Cora", "Yolanda", "Kara", "Essie", "Tasha", "Alyssa", "Daisy", "Summer", "Jenny", "Ariel", "Hope", "Skyler", "Riley", "Reagan", "Piper", "Sydney", "Kylie", "Mackenzie", "Brooklyn", "Zoey", "Taylor", "Alexis", "Jordan", "Harper", "Peyton", "Avery", "Quinn", "Bailey", "Payton", "Morgan", "Kennedy", "Emerson", "Addison", "Reese", "Finley", "Rowan", "Charlie", "Sawyer", "Elliot", "Emery"]
last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker", "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy", "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson", "Bailey", "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson", "Watson", "Brooks", "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza", "Ruiz", "Hughes", "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers", "Long", "Ross", "Foster", "Jimenez", "Powell", "Jenkins", "Perry", "Russell", "Sullivan", "Bell", "Coleman", "Butler", "Henderson", "Barnes", "Gonzales", "Fisher", "Vasquez", "Simmons", "Romero", "Jordan", "Patterson", "Alexander", "Hamilton", "Graham", "Reynolds", "Griffin", "Wallace", "Moreno", "West", "Cole", "Hayes", "Bryant", "Herrera", "Gibson", "Ellis", "Tran", "Medina", "Aguilar", "Stevens", "Murray", "Ford", "Castro", "Marshall", "Owens", "Harrison", "Fernandez", "McDonald", "Woods", "Washington", "Kennedy", "Wells", "Vargas", "Henry", "Chen", "Freeman", "Webb", "Tucker", "Guzman", "Burns", "Crawford", "Olson", "Simpson", "Porter", "Hunter", "Gordon", "Mendez", "Silva", "Shaw", "Snyder", "Mason", "Dixon", "Singh", "Schmidt", "Wheeler", "Warren", "Watkins", "Larson", "Carlson", "Harper", "George", "Curtis", "Neal", "Austin", "Peters", "Kelley", "Franklin", "Lawson", "Fields", "Gutierrez", "Ryan", "Schneider", "Banks", "Mendoza", "Meyer", "Castillo", "Ortega", "Gregory", "Garza", "Harvey", "Luna", "Ferguson", "Harvey", "George", "Lawrence", "Alvarado", "Russell", "Bates", "Castillo", "Mcdonald", "Suarez", "Mccoy", "Smith", "Chang", "Sullivan", "Wallace", "Huynh", "Hicks", "Wilson", "Barr", "Mcdaniel", "Lopez", "Stevenson", "Velasquez", "Khan", "Rivas", "Kramer", "Santos", "Gallagher"]
street_names = ["Main Street", "Elm Street", "Oak Avenue", "Maple Lane", "Broadway", "Washington Street", "Park Avenue", "Cedar Drive", "Pine Street", "First Street", "Second Avenue", "Third Street", "Fourth Avenue", "Fifth Street", "Maple Street", "Church Street", "High Street", "Spring Street", "Center Street", "Front Street", "Pleasant Avenue", "Sunset Boulevard", "River Road", "Lake Street", "Chestnut Street", "Hillcrest Drive", "Birch Street", "Forest Drive", "Meadow Lane", "Grove Avenue", "Sycamore Lane", "West End Avenue", "Market Street", "Willow Street", "Ridge Road", "Central Avenue", "Parkway Drive", "Holly Street", "Hillside Avenue", "Riverside Drive", "State Street", "Grand Avenue", "College Avenue", "Mountain View Drive", "Prospect Street", "Valley Road", "Court Street", "Bridge Street", "Sunrise Avenue", "Linden Street", "Main Avenue", "North Street", "South Street", "East Street", "West Street", "Cherry Lane", "Meadow Lane", "Glenwood Avenue", "Whispering Pines Lane", "Mason Street", "Blossom Lane", "Harbor Drive", "Creek Road", "Victory Lane", "Magnolia Avenue", "Green Street", "Lakeside Drive", "Lincoln Avenue", "Park Place", "Railroad Avenue", "Avenue A", "Avenue B", "Avenue C", "Avenue D", "Avenue E", "Avenue F", "Avenue G", "Avenue H", "Avenue I", "Avenue J", "Avenue K", "Avenue L", "Avenue M", "Avenue N", "Avenue O", "Avenue P", "Avenue Q", "Avenue R", "Avenue S", "Avenue T", "Avenue U", "Avenue V", "Avenue W", "Avenue X", "Avenue Y", "Avenue Z", "Market Place", "Harbor Street", "Main Plaza", "Ocean Avenue", "Rosewood Lane", "Winding Way", "Parkside Drive", "Bayview Drive", "Crescent Street", "Colonial Drive", "Ridge Avenue", "Grandview Drive", "Manor Road", "Summer Street", "Spruce Avenue", "Sunny Lane", "Brookside Drive", "Acorn Avenue", "Cottonwood Lane", "Evergreen Drive", "Sycamore Lane", "River Street", "Lakeview Drive", "Oak Street", "Hickory Lane", "Pine Street", "Cedar Street", "Elm Avenue", "Aspen Lane", "Sunset Avenue", "Holly Drive", "Meadow Lane", "Vine Street", "Poplar Avenue", "Bluebird Lane", "Fernwood Avenue", "Hillcrest Avenue", "Orchard Drive", "Willow Lane", "Cottage Street", "Wisteria Lane", "Maple Avenue", "Dogwood Lane", "Beech Street", "Juniper Avenue", "Redwood Avenue", "Mulberry Street", "Larch Street", "Sycamore Avenue", "Magnolia Street", "Peachtree Street", "Tulip Lane", "Juniper Street", "Pond Street", "Lilac Lane", "Spruce Street", "Cypress Avenue", "Hawthorn Street", "Birch Street", "Laurel Lane", "Acacia Avenue", "Linden Avenue", "Pinehurst Drive", "Birchwood Drive", "Fox Hollow Lane", "Cedar Lane", "Cherry Street", "School Street", "Deerfield Lane", "Lakeshore Drive", "Forest Avenue", "Hazel Street", "Juniper Lane", "Ash Street", "Mossy Oak Drive", "Locust Street", "Hillcrest Drive", "Rosewood Drive", "Woodland Avenue", "River Lane", "Country Club Road", "Evergreen Lane", "Meadowbrook Lane", "Buckeye Lane", "Silver Maple Drive", "Apple Blossom Lane", "Hickory Lane", "Sunset Lane", "Parkside Avenue", "Spruce Lane", "Oakwood Drive", "Lakeside Drive", "Elm Street", "Forest Lane", "Ridge Lane", "Spring Lane", "Primrose Lane", "Dogwood Drive", "River View Drive", "Pinecrest Avenue", "Holly Court", "Hilltop Road", "Grove Street", "Magnolia Lane", "Maple Avenue", "Chestnut Street", "Glenwood Drive", "Winding Lane", "Sycamore Street", "River Street", "Lakeside Avenue", "Park Place", "Woodland Drive", "Willow Street", "Mountain View Drive", "Sycamore Drive", "Birch Lane", "Maple Street", "Elm Avenue", "River Road", "Lakeview Drive", "Main Street", "Sunset Boulevard", "Oak Lane", "Forest Drive", "Cedar Lane", "Pine Street", "Ridge Avenue", "Spring Street", "Cottage Lane", "Grove Avenue", "Mountain View Road", "Maple Lane", "Chestnut Avenue", "Winding Way", "Brookside Avenue", "Pond Road", "Hilltop Drive", "Dogwood Lane", "River Lane", "Lake Avenue", "Sunrise Avenue", "Ocean Avenue", "Birchwood Lane", "Holly Avenue", "Greenwood Avenue", "Harbor Drive", "Willow Lane", "Hillcrest Lane", "Valley View Road", "Woodland Road", "Cedar Avenue", "Pine Lane", "Main Street", "Elm Avenue", "Oak Street", "Maple Lane", "Broadway", "Washington Street", "Park Avenue", "Cedar Drive", "Pine Street", "First Street", "Second Avenue", "Third Street", "Fourth Avenue", "Fifth Street"]
towns = ["Galena", "Carbondale", "Galesburg", "Jacksonville", "Dixon", "Angola", "Madison", "Bedford", "Jasper", "Peru", "Decorah", "Pella", "Fairfield", "Maquoketa", "Winterset", "Dodge City", "Hays", "Emporia", "Hutchinson", "Liberal", "Traverse City", "Marquette", "Mount Pleasant", "Holland", "Sault Ste. Marie", "Alton", "Quincy", "Freeport", "Kankakee", "DeKalb", "Vincennes", "Anderson", "Muncie", "Valparaiso", "Kokomo", "Muscatine", "Ottumwa", "Fort Dodge", "Sioux City", "Council Bluffs", "Dubuque", "Waterloo", "Leavenworth", "Salina", "Great Bend", "Newton", "Coffeyville", "Farmington Hills", "Royal Oak", "Sterling Heights", "Novi", "Saginaw", "Ypsilanti", "Holland", "Plymouth", "Marshall", "Emporia", "Hays", "Hutchinson", "Atchison", "Lawrence", "Manhattan", "Abilene", "Dodge City", "Salina", "Seward", "Liberal", "Garden City", "Winfield", "Emporia", "Junction City", "Chanute", "Marshalltown", "Burlington", "Cedar Rapids", "Mason City", "Ottumwa", "Oskaloosa", "Fort Dodge", "Clinton", "Keokuk", "Muscatine", "Kewanee", "Galesburg", "Dixon", "Freeport", "Pontiac", "Mount Pleasant", "Charleston", "Marion", "Goshen", "Marion", "Crawfordsville", "Frankfort", "Michigan City", "Anderson", "Bedford", "Vincennes", "New Albany", "Columbus", "Warsaw", "Crown Point", "Richmond", "Michigan City", "Logansport", "Crawfordsville", "Shelbyville", "La Porte", "Plymouth", "Goshen", "Crown Point", "Franklin", "Lebanon", "Greencastle", "Crawfordsville", "Seymour", "Vincennes", "Bedford", "Jasper", "Madison", "Washington", "Peru", "Portland", "Decatur", "Logansport", "Angola", "Nappanee", "Scottsburg", "Lawrenceburg", "New Haven", "Connersville", "Zionsville", "Peru", "Hartford City", "Rensselaer", "Frankfort", "Madison", "Bedford", "Jasper", "Wabash", "Decatur", "Angola", "North Vernon", "Scottsburg", "Wabash", "Batesville", "Bedford", "Jasper", "North Vernon", "Madison", "Rochester", "Austin", "Owatonna", "Faribault", "Winona", "Willmar", "Marshall", "Hibbing", "Bemidji", "Brainerd", "Fergus Falls", "Crookston", "Worthington", "Fargo", "Grand Forks", "Minot", "Bismarck", "Dickinson", "Jamestown", "Devils Lake", "Valley City", "Belle Fourche", "Sturgis", "Spearfish", "Hot Springs", "Pierre", "Yankton", "Vermillion", "Watertown", "Huron", "Brookings", "Aberdeen", "Madison", "Milbank", "Mobridge", "Winner", "Canton", "Lead", "Deadwood", "Philip", "Pierre", "Fort Pierre", "Mission", "Kadoka", "Martin", "Chamberlain", "Platte", "Geddes", "Murdo", "Buffalo", "Bison", "Faulkton", "Redfield", "Clark", "Webster", "Clear Lake", "Sisseton", "Waubay", "Britton", "Lake City", "De Smet", "Elkton", "Estelline", "Highmore", "Selby", "Roslyn", "Roscoe", "Leola", "Java", "Bowdle", "Eureka", "Hosmer", "Langford", "Warner", "Cresbard", "Herreid", "Pollock", "McLaughlin", "Wakpala", "McIntosh", "Mound City", "Timber Lake", "Pollock", "Strasburg", "Zeeland", "Ashley", "Wishek", "Gackle", "Kulm", "Edgeley", "Linton", "Hazelton", "Steele", "Tappen", "Napoleon", "Garrison", "Riverdale", "Washburn", "Stanton", "Max", "Coleharbor", "Underwood", "Wilton", "Turtle Lake", "McClusky", "Strasburg", "Zeeland", "Hague", "Balfour", "Carpio", "Granville", "Karlsruhe", "Voltaire", "Glenburn", "Mohall", "Surrey", "Towner", "Bantry", "Deering", "Norwich", "Antler", "Westhope", "Newburg", "Lansford", "Williston", "Watford City", "Stanley", "Tioga", "Bowbells", "Crosby", "Ray", "Powers Lake", "Wildrose", "Fargo", "West Fargo", "Grand Forks", "Minot", "Bismarck", "Dickinson", "Jamestown", "Devils Lake", "Valley City", "Wahpeton", "Grafton", "Mandan", "Williston", "Beulah", "Horace", "Hazen", "Lincoln", "Belcourt", "Bottineau", "New Town", "Carrington", "Langdon", "Harvey", "Lisbon", "Oakes", "Park River", "Rolla", "Rugby", "Ellendale", "Linton", "Edgeley", "Hebron", "Stanley", "Washburn", "Garrison", "Underwood", "New Salem", "Elgin", "Mott", "Hettinger", "Mohall", "Glen Ullin", "Drayton", "Killdeer", "Richardton", "Northwood", "Hankinson", "Turtle Lake", "Munich", "Ashley", "Fairmount", "Kenmare", "Wishek", "Lidgerwood", "Gackle", "Underwood", "Walhalla", "New Leipzig", "Leeds", "Strasburg", "Glenburn", "Center", "Medina", "Golva", "Buxton", "Reynolds", "Finley", "Rutland", "Ardoch", "Niagara", "Rogers", "Hannah", "Amenia", "McClusky", "Alexander", "Almont", "Pettibone", "Buchanan", "Wales", "Wyndmere", "Mandan", "New Salem", "Glen Ullin", "Hebron", "Steele", "Beach", "Richardton", "Taylor", "Hazen", "Scranton", "Golva", "Halliday", "Glenburn", "Plaza", "Pick City", "Bottineau", "Stanton", "Drake", "New Leipzig", "Parshall", "Mott", "Rolette", "Harvey", "Strasburg", "Underwood", "Mapleton", "Washburn", "Max", "Sawyer", "Rutland", "Sibley", "Lignite", "Reeder", "Surrey", "Hebron", "Glenburn", "Hazelton", "Balfour", "Marmarth", "Martin", "Petersburg", "Brocket", "Prairie Rose", "Christine", "Almont", "Absaraka", "Buchanan", "Landa", "Plaza", "Tuttle", "Pettibone", "Harwood", "Arnegard", "LaMoure", "Fort Totten", "Westhope", "Glenburn", "Max", "Riverdale", "Stanley", "Forman", "Forest River", "Deering", "Carson", "Berthold", "Rhame", "Balta", "Hoople", "Ludden", "Scranton", "Donnybrook", "Fingal", "Enderlin", "Arthur", "Raub", "Regent", "Oriska", "Marion", "Thompson", "Dunseith", "Medora", "Wimbledon", "Lidgerwood", "Nekoma", "Hettinger", "Edgeley", "Pekin", "Flasher", "Lignite", "Hazen", "Fort Yates", "Litchville", "York", "Ray", "Hampden", "Edmore", "Edinburg", "Neche", "Wheatland", "Hazelton", "Glenburn", "Reeder", "Hettinger", "Lakota", "Spiritwood", "White Earth", "Forbes", "Page", "Sheldon", "Caledonia", "Binford", "South Heart", "Des Lacs", "Reile's Acres", "Grenora", "North River", "Milton", "Bowdon", "Portland", "Sykeston", "Tolna", "Zeeland", "Luverne", "Sheyenne", "Golva", "Medina", "Selfridge", "Lansford", "Elliott", "Wimbledon", "Golden Valley", "Kief", "Maddock", "Fort Ransom", "Regan", "Golva", "Raleigh", "Michigan", "Lefor", "Tuttle", "Oriska", "Pettibone", "Wyndmere", "Strasburg", "Anamoose", "Braddock", "Deering", "Sheyenne", "Scranton", "Gackle", "Arnegard", "Bantry", "Venturia", "Cayuga", "Elliott", "Ardoch", "Grano", "Rutland", "Ross", "Lankin", "Epping", "Tappen", "Tower City", "Hillsboro", "Glen Ullin", "Richardton", "Petersburg", "Hebron", "Burlington", "Plaza", "Cathay", "Wimbledon", "Ross", "Fessenden", "St. Thomas", "Westhope", "Deering", "Hannaford", "South Heart", "Buffalo", "Dunn Center", "Alice", "Glenburn", "Dawson", "Amidon", "Pingree", "White Earth", "Knox", "Edinburg", "Golden Valley", "Hurdsfield", "Elliott", "Aneta", "Reeder", "Milton", "Ray", "Ross", "Minto", "Oriska", "Crary", "Abercrombie", "Driscoll", "Niagara", "New Leipzig", "Taylor", "Rutland", "West Fargo", "Fargo", "Bismarck", "Grand Forks", "Minot", "Mandan", "Dickinson", "Jamestown", "Williston", "Wahpeton", "Devils Lake", "Valley City", "Beulah", "Hazen", "Grafton", "Lincoln", "Belcourt", "New Town", "Watford City", "Lisbon", "Oakes", "Harvey", "Carrington", "Mayville", "Langdon", "Linton", "Bowman", "Killdeer", "Bottineau", "Rolla", "Velva", "Rolette", "Cavalier", "Ellendale", "Mott", "Hettinger", "Glen Ullin", "Beach", "Stanley", "Forman", "Kindred", "Larimore", "Thompson", "Edgeley", "Crosby", "LaMoure", "Hillsboro", "Northwood", "Hankinson", "Lidgerwood", "Underwood", "Garrison", "Mapleton", "Richardton", "Fessenden", "New Salem", "Tioga"]
zipcodes = ["90210", "10001", "30301", "60601", "75001", "84101", "33101", "94101", "10002", "20001", "30302", "60602", "75002", "84102", "33102", "94102", "10003", "20002", "30303", "60603", "75003", "84103", "33103", "94103", "10004", "20003", "30304", "60604", "75004", "84104", "33104", "94104", "10005", "20004", "30305", "60605", "75005", "84105", "33105", "94105", "10006", "20005", "30306", "60606", "75006", "84106", "33106", "94106", "10007", "20006", "30307", "60607", "75007", "84107", "33107", "94107", "10008", "20007", "30308", "60608", "75008", "84108", "33108", "94108", "10009", "20008", "30309", "60609", "75009", "84109", "33109", "94109", "10010", "20009", "30310", "60610", "75010", "84110", "33110", "94110", "10011", "20010", "30311", "60611", "75011", "84111", "33111", "94111", "10012", "20011", "30312", "60612", "75012", "84112", "33112", "94112", "10013", "20012", "30313", "60613", "75013", "84113", "33113", "94113", "10014", "20013", "30314", "60614", "75014", "84114", "33114", "94114", "10015", "20014", "30315", "60615", "75015", "84115", "33115", "94115", "10016", "20015", "30316", "60616", "75016", "84116", "33116", "94116", "10017", "20016", "30317", "60617", "75017", "84117", "33117", "94117", "10018", "20017", "30318", "60618", "75018", "84118", "33118", "94118", "10019", "20018", "30319", "60619", "75019", "84119", "33119", "94119", "10020", "20019", "30320", "60620", "75020", "84120", "33120", "94120"]
countries = ["usa"]
referrers = ["google", "meta", "organic", "billboard", "referral", "email", "other"]
#--------------------------------------FUNCTIONS------------------------------------------

def evaluate_gender():
    genders = ["Male", "Female"]
    return random.choice(genders)

def generate_name(gender, first_names, last_names):
    if gender == "Male":
        first_name = random.choice(male_first_names)
        last_name = random.choice(last_names)
    elif gender == "Female":
        first_name = random.choice(female_first_names)
        last_name = random.choice(last_names)
    full_name = f"{first_name} {last_name}"
    return full_name

def generate_email(name):
    name_parts = name.lower().split(" ")
    random.shuffle(name_parts)
    name = ".".join(name_parts)
    if random.random() < 0.5:
        name = name.replace(".", "")
    domain = random.choice(email_domains)
    email = f"{name}@{domain}"
    return email

def generate_cc_number():
    def generate_random_luhn_valid_card_number():
        card_prefixes = {
            "Visa": ["4"],
            "MasterCard": ["51", "52", "53", "54", "55"],
            "American Express": ["34", "37"],
            "Discover": ["6011", "622126", "622925", "644", "645", "646", "647", "648", "649", "65"]
        }
        length_dict = {
            "Visa": 16,
            "MasterCard": 16,
            "American Express": 15,
            "Discover": 16
        }

        card_type = random.choice(list(card_prefixes.keys()))
        prefix = random.choice(card_prefixes[card_type])
        length = length_dict[card_type]

        num_digits_to_generate = length - len(prefix) - 1  # Leave space for the check digit
        base_part = prefix + ''.join([str(random.randint(0, 9)) for _ in range(num_digits_to_generate)])

        # Calculate Luhn check digit
        def digits_of(n):
            return [int(d) for d in str(n)]
        
        def luhn_checksum(card_number):
            digits = digits_of(card_number)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d*2))
            return checksum % 10
        
        check_digit = luhn_checksum(int(base_part) * 10)
        check_digit = 0 if check_digit == 0 else 10 - check_digit
        return f"{base_part}{check_digit}", card_type
    
    card_number, card_type = generate_random_luhn_valid_card_number()

    cvv_length = 3 if card_type != "American Express" else 4  # AmEx cards have a 4-digit CVV
    cvv = ''.join([str(random.randint(0, 9)) for _ in range(cvv_length)])

    # Generate expiration date 2 to 4 years ahead of the current date
    def generate_exp_date_details():
        current_year = datetime.now().year
        exp_year = random.randint(current_year + 2, current_year + 4)
        exp_month = random.randint(1, 12)

        month_names = ["January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]
        full_month_name = month_names[exp_month - 1]
        full_month_name_prefixed = f"{exp_month} {full_month_name}"

        return {
            "mm/yy": f"{exp_month:02}/{exp_year - 2000}",
            "number_month": full_month_name_prefixed,
            "yyyy": str(exp_year)  # Ensure this is a string for selection purposes
        }

    exp_details = generate_exp_date_details()
    
    # Correctly package the details for returning
    return {
        "card_number": card_number,
        "cvv": cvv,
        "exp_month": exp_details["number_month"].split(' ')[0],  # Just the numeric part for month selection
        "exp_month_full": exp_details["number_month"],  # Full month name with prefix, if needed
        "exp_year": exp_details["yyyy"],  # Full year
    }

def generate_ssn():
    ssn = [str(random.randint(1, 9))] + [str(random.randint(0, 9)) for _ in range(1, 3)] + [str(random.randint(0, 9)) for _ in range(2)] + [str(random.randint(0, 9)) for _ in range(4)]
    ssn = '-'.join(''.join(ssn[i:i+3]) if i != 3 else ''.join(ssn[i:i+2]) for i in range(0, 9, 3))
    return ssn

def generate_street():
    house_number = ''.join(random.choices('0123456789', k=3))
    street = random.choice(street_names)
    return f"{house_number} {street}"

def generate_phone_number(area_codes):
    area_code = random.choice(area_codes)
    number = ''.join(random.choices('0123456789', k=7))
    return f"{area_code}-{number[:3]}-{number[3:]}"

def generate_full_address():
    state_info = random.choice(locations)
    street = generate_street()
    town = random.choice(towns)
    zip_code = random.choice(state_info["zips"])
    full_address = f"{street}, {town}, {state_info['abbr']} {zip_code}"
    phone = generate_phone_number(state_info["area_codes"])
    return full_address, phone, town, state_info["abbr"], zip_code, state_info

def generate_person_info():
    gender = evaluate_gender()
    full_name = generate_name(gender, male_first_names, last_names)
    first_name, last_name = full_name.split(' ', 1)
    # ssn = generate_ssn()
    address, phone_number, town, state, zipcode, _ = generate_full_address()
    email = generate_email(full_name)
    referrer = random.choice(referrers)
    country = random.choice(countries)

    return {
        "gender": gender,
        "first_name": first_name,
        "last_name": last_name,
        "address": address,
        "city": town,
        "state": state,
        "country": country,
        "zipcode": zipcode,
        "phone": phone_number,
        "email": email,
        "referrer": referrer

    }

def show_person_info():
    person_info = generate_person_info()
    for key, value in person_info.items():
        print(f"{key}: {value}")

def random_time_interval():
    return random.randint(1, 60)

# Main Function to Generate Info
def generate_person():
    person_info = generate_person_info()
    return person_info

