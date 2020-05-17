from auxo_mount_olympus.ui.mainw import Ui_MainWindow
from auxo_mount_olympus.gen import gen 

import sys
from PySide2.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QHeaderView, QMessageBox
from PySide2.QtCore import QFile


from pathlib import Path    # TODO: Switch all the path stuff to pathlib.Path for OOP
import shutil
import datetime 
import os
import glob 


AUXO_OLYMPUS_DIR = "../../auxo_olympus"


# MARK: Utility 
def shorten_string(string, num_chars=50) -> str: 
    """
    Shortens a description to num_chars and adds ellipsis 
    """
    if len(string) > num_chars: 
        return '{:.{num_chars}}'.format(string, num_chars=num_chars) + '...'
    return string 

# MARK: Auxo Mount Olympus 
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # init 
        # self.populateTable()

    def statusPrint(self, msg): 
        """
        Prints to the shared status box 
        """
        now = datetime.datetime.now() 
        formatted_time = now.strftime("%m-%d %H:%M:%S")
        msg = f"{formatted_time} > {msg}" 
        self.ui.statusTextBrowser.append(msg)


#################################### SERVICES TAB ###################################################
    def findServices(self) -> dict: 
        """finds all the serviceExes.txts within the AUXO_OLYMPUS_DIR folder

        Returns:
            dict -- service name with its name, author, description and last_modified 
        """
        services_dir = f'{AUXO_OLYMPUS_DIR}/lib/services'
        all_services = [os.path.join(services_dir, o) for o in os.listdir(services_dir) if os.path.isdir(os.path.join(services_dir,o))]
        
        services = {}
        for service_dir in all_services: 
            for root, dirs, files in os.walk(service_dir): 
                for f in files: 
                    if f.startswith("serviceExe") and f.endswith(".txt"): 
                        read_file = open(os.path.join(root, f), "r")
    
                        name = read_file.readline().split(":")[1].strip()
                        author = read_file.readline().split(":")[1].strip()
                        last_modified = (":".join(read_file.readline().split(":")[1:])).strip()
                        description = shorten_string(read_file.read().split(":")[1].strip()) 

                        services[name] = {"name": name, "author": author, "description": description, "last_modified": last_modified}
                        read_file.close() 
        
        return services

    def populateTable(self, verbose=True):
        """Populates the table with all the available services 
        """
        if verbose: 
            msg = f"(Re)loaded available services"
            self.statusPrint(msg)

        services = self.findServices()
        num_services = len(services)
        self.ui.servicesTable.setRowCount(num_services)
        for i, (_, contents) in enumerate(services.items()): 
            """
            0 -> service name 
            1 -> author 
            2 -> description 
            3 -> last modified
            """
            name = QTableWidgetItem(contents["name"])
            author = QTableWidgetItem(contents["author"])
            description = QTableWidgetItem(contents["description"])
            last_modifed = QTableWidgetItem(contents["last_modified"])

            self.ui.servicesTable.setItem(i, 0, name) 
            self.ui.servicesTable.setItem(i, 1, author) 
            self.ui.servicesTable.setItem(i, 2, description) 
            self.ui.servicesTable.setItem(i, 3, last_modifed) 

        # To remove the vertical lines 
        self.ui.servicesTable.setStyleSheet('QTableView::item {border-bottom: 1px solid #d6d9dc;}')    
        # To resize to fill the main window 
        self.ui.servicesTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # self.ui.servicesTable.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)      # if you want rows to divide evenly 
        # fixed row heights 
        self.ui.servicesTable.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.ui.servicesTable.verticalHeader().setDefaultSectionSize(40)

    def launchServiceExe(self): 
        """
        Takes the selected serviceExe row in the servicesTable, and runs it!
        """
        index = self.ui.servicesTable.selectionModel().currentIndex()
        row: int = index.row() 
        # to get the service name
        service_name = index.sibling(row, 0).data()
        msg = f"Launching service: {service_name}"
        self.statusPrint(msg)

        # TODO: Connect this to the actual executor within Olympus (LAUNCH THE SERVICE)

    def deleteServiceExe(self): 
        """
        Deletes the selected serviceExe
        """
        index = self.ui.servicesTable.selectionModel().currentIndex()
        row: int = index.row() 
        # to get the service name
        service_name = index.sibling(row, 0).data()

        # Ask for confirmation, if yes, then delete 
        response = self.onShowQuestion(msg=f"Delete {service_name}? Can't undo!")
        if response: 
            service_name_compressed = "".join(service_name.split())
            # Delete the service by deleting the entire folder 
            service_dirpath = Path(AUXO_OLYMPUS_DIR, f"lib/services/serviceExe{service_name_compressed}")
            if service_dirpath.exists() and service_dirpath.is_dir():
                shutil.rmtree(service_dirpath)

            msg = f"Deleted service: {service_name}"
            self.statusPrint(msg)

            # changes the table, so repopulate the table 
            self.populateTable(verbose=False)

    def editServiceExe(self):
        """
        Opens the folder for the selected serviceExe 
        """
        index = self.ui.servicesTable.selectionModel().currentIndex()
        row: int = index.row() 
        # to get the service name
        service_name = index.sibling(row, 0).data()

        msg = f"Opening service {service_name} folder -- please reload services when done editing"
        self.statusPrint(msg) 

    def onShowQuestion(self, msg) -> bool:
        """
        Show a question
        """
        flags = QMessageBox.StandardButton.Yes
        flags |= QMessageBox.StandardButton.Cancel
        response = QMessageBox.question(self, "Question", msg, flags)

        if response == QMessageBox.Yes: 
            return True 
        return False 

#################################### CUSTOM TAB ###################################################
    def servicesGenerateButtonPressed(self):
        """
        LineEdits: 
        serviceNameLineEdit
        authorLineEdit
        descriptionPlainTextEdit
        agentLaunchFileTextEdit
        """

        service_name = self.ui.serviceNameLineEdit.text()
        author = self.ui.authorLineEdit.text()
        description = self.ui.descriptionPlainTextEdit.toPlainText()
        launch_file = self.ui.agentLaunchFileTextEdit.toPlainText() 

        try: 
            self.generateServiceSkeleton(service_name, author, description, launch_file)
        except:
            return 

        msg = f"Generated service: {service_name} ({author})"
        self.statusPrint(msg)

         # changes the table, so repopulate the table 
        self.populateTable(verbose=False)
    
    def generateServiceSkeleton(self, service_name, author, description, launch_file):
        # gen.generate(directory, service_name, author, description, last_modified=None, verbose=True):

        # TODO: Implement the launch file as well   
        if launch_file: 
            pass

        service_topdirpath = Path(AUXO_OLYMPUS_DIR, f"lib/services")
        gen.generate(service_topdirpath, service_name, author, description, verbose=False)



if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
