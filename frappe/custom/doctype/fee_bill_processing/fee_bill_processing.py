# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime
from frappe.utils import money_in_words

class FeeBillProcessing(Document):
	def on_submit(self):
		try:
			for obj in self.student_details:
				fee = dict()
				student = obj.student_name
				institution = self.company
				posting_date = datetime.now().date().strftime('%Y-%m-%d')
				posting_time = datetime.now().time().strftime("%H:%M:%S")
				due_date = self.bill_date

				# program_enrollment = frappe.get_doc('Program Enrollment',{'academic_year':self.academic_year,'docstatus':1,'student_name':student},['name'])

				structure = frappe.get_doc('Student Structure Allocation',{'student':obj.student,'docstatus':1,'custom_enabled':1},['*'])

				struct = frappe.get_doc('Fee Structure',{'name':structure.fee_structure})
				fee_structure_componensts = structure.fee_structure_components
				
				#discount_policies
				discount_policies = frappe.get_doc('Student Discount Policy Allocation',{'student':obj.student})
				

				policies = frappe.get_all('Custom Discount Policy',{'parent':discount_policies.get('name')},['fee_category','discount','discount_in_amount','remarks'])

				components_list = frappe.db.get_all('Fee Component',{'parent':structure.name},['fees_category','amount'])
				total_discount = 0
				total_fee = 0
				for component in components_list:
						total_fee = total_fee + component['amount']
				
				for p in policies:
					if p['discount']:
						for component in components_list:
							if p['fee_category'] == component['fees_category']:
								total_discount = total_discount + ((p['discount']/100)*component['amount'])
					if p['discount_in_amount']:
						total_discount = total_discount + p['discount_in_amount']

				#fee_adjustmentss
				fee_adjustments = frappe.get_doc('Student Fee Adjustment',{'student':obj.student})
				adjustments = fee_adjustments.get('student_fee_adjustment_detail')

				total_adjustments = 0
				for a in adjustments:
					if a.get('amount'):
						total_adjustments = total_adjustments + a.get('amount')

				total_amount = 0
				if structure.total_amount:
					total_amount = float(structure.total_amount) - float(total_discount) + float(total_adjustments)
				
				fees = {'doctype':'Fees',
						'student': obj.student,
						'company': institution,
						'posting_date': posting_date,
						'posting_time': posting_time,
						'due_date': due_date,
						'academic_year': self.academic_year,
						'program_enrollment': 'ABC',
						'fee_structure':structure.fee_structure,
						'components': fee_structure_componensts,
						'custom_discount_policies':policies,
						'custom_fee_adjustments': adjustments,
						'grand_total':total_amount,
						'grand_total_in_words': money_in_words(total_amount),
						'outstanding_amount':total_amount,
						'custom_total_adjustment':float(total_adjustments),
						'custom_total_fee':float(total_fee),
						'custom_total_discount':float(total_discount)
						}

				doc = frappe.get_doc(fees)
				doc.flags.ignore_permissions = True
				doc.save()

				# self.discount_policies = policies
				# self.fee_adjustments = adjustments
				frappe.db.commit()
		except Exception as e:
			frappe.log_error(frappe.get_traceback() , 'Error While Bill Processing')
			frappe.throw('Error Occured')
			frappe.db.rollback()



