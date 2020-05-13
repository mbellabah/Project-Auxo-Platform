from auxo_mount_olympus.ui.mainw import Ui_MainWindow

import sys
from PySide2.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QHeaderView
from PySide2.QtCore import QFile


import datetime 
import os
import glob 

AUXO_OLYMPUS_DIR = "../../auxo_olympus"


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

    # MARK: Services tab 
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
                        last_modified = read_file.readline().split(":")[1].strip()
                        description = read_file.read().split(":")[1].strip()

                        services[name] = {"name": name, "author": author, "description": description, "last_modified": last_modified}
                        read_file.close() 
        
        return services

    def populateTable(self):
        """Populates the table with all the available services 
        """
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
        self.ui.servicesTable.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def launchServiceExe(self): 
        """Takes the selected serviceExe row in the servicesTable, and runs it!
        """
        index = self.ui.servicesTable.selectionModel().currentIndex()
        row: int = index.row() 
        # to get the service name
        service_name = index.sibling(row, 0).data()
        msg = f"Launching service: {service_name}"
        self.statusPrint(msg)

        # TODO: Connect this to the actual executor within Olympus (LAUNCH THE SERVICE)

#######################################################################################################

    # MARK: Custom tab 
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

        msg = f"Generating service: {service_name} ({author})"
        self.statusPrint(msg)

        self.generateServiceSkeleton(service_name, author, description, launch_file)
    
    def generateServiceSkeleton(self, service_name, author, description, launch_file):

        # TODO: Implement and connect to the code skeleton generator 
        if launch_file: 
            pass
        pass 


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
