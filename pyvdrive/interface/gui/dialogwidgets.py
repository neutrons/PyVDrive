from PyQt4.QtGui import QDialog, QVBoxLayout, QDialogButtonBox, QDateTimeEdit, QApplication
from PyQt4.QtCore import Qt, QDateTime

# Customized dialog widgets
__author__ = 'wzz'


class DateDialog(QDialog):
    def __init__(self, parent = None):
        super(DateDialog, self).__init__(parent)

        layout = QVBoxLayout(self)

        # nice widget for editing the date
        self.datetime = QDateTimeEdit(self)
        self.datetime.setCalendarPopup(True)
        self.datetime.setDateTime(QDateTime.currentDateTime())
        layout.addWidget(self.datetime)

        # OK and Cancel buttons
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        layout.addWidget(self.buttons)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    # get current date and time from the dialog
    def dateTime(self):
        return self.datetime.dateTime()

# static method to create the dialog and return (date, time, accepted)
def getDateTime(parent = None):
    dialog = DateDialog(parent)
    result = dialog.exec_()
    date = dialog.dateTime()
    return (date.date(), date.time(), result == QDialog.Accepted)


if __name__ == '__main__':
    getDateTime()
