package dev.vale.simplifying

import dev.vale.finalast.{FunctionH, Local, NeverH, PureH, UserFunctionH, VariableIdH}
import dev.vale.typing.Hinputs
import dev.vale.typing.ast.{ExternT, FunctionHeaderT, FunctionT, IFunctionAttributeT, PrototypeT, PureT, UserFunctionT}
import dev.vale.typing.names.{FullNameT, IVarNameT}
import dev.vale.{vassert, vfail, vimpl, vwat}
import dev.vale.finalast._
import dev.vale.{finalast => m}
import dev.vale.typing._
import dev.vale.typing.ast._
import dev.vale.typing.names.IVarNameT

class FunctionHammer(
    typeHammer: TypeHammer,
    nameHammer: NameHammer,
    structHammer: StructHammer) {
  val expressionHammer =
    new ExpressionHammer(typeHammer, nameHammer, structHammer, this)

  def translateFunctions(
    hinputs: Hinputs,
    hamuts: HamutsBox,
    functions2: Vector[FunctionT]):
  (Vector[FunctionRefH]) = {
    functions2.foldLeft((Vector[FunctionRefH]()))({
      case ((previousFunctionsH), function2) => {
        val (functionH) = translateFunction(hinputs, hamuts, function2)
        Vector(functionH) ++ previousFunctionsH
      }
    })
  }

  def translateFunction(
    hinputs: Hinputs,
    hamuts: HamutsBox,
    function2: FunctionT):
  (FunctionRefH) = {
//    opts.debugOut("Translating function " + function2.header.fullName)
    hamuts.functionRefs.get(function2.header.toPrototype) match {
      case Some(functionRefH) => functionRefH
      case None => {
        val FunctionT(
            header @ FunctionHeaderT(humanName, attrs2, params2, returnType2, _),
            body) = function2;

        val (prototypeH) = typeHammer.translatePrototype(hinputs, hamuts, header.toPrototype);
        val temporaryFunctionRefH = FunctionRefH(prototypeH);
        hamuts.forwardDeclareFunction(header.toPrototype, temporaryFunctionRefH)

        val locals =
          LocalsBox(
            Locals(
              Map[FullNameT[IVarNameT], VariableIdH](),
              Set[VariableIdH](),
              Map[VariableIdH,Local](),
              1));
        val (bodyH, Vector()) =
          expressionHammer.translate(hinputs, hamuts, header, locals, body)
        vassert(locals.unstackifiedVars.size == locals.locals.size)
        val resultCoord = bodyH.resultType
        if (resultCoord != prototypeH.returnType) {
          resultCoord.kind match {
            case NeverH(_) => // meh its fine
            case _ => {
              vfail(
                "Result of body's instructions didnt match return type!\n" +
                  "Return type:   " + prototypeH.returnType + "\n" +
                  "Body's result: " + resultCoord)
            }
          }
        }

        val isAbstract = header.getAbstractInterface.nonEmpty
        val isExtern = header.attributes.exists({ case ExternT(packageCoord) => true case _ => false })
        val attrsH = translateFunctionAttributes(attrs2.filter(a => !a.isInstanceOf[ExternT]))
        val functionH = FunctionH(prototypeH, isAbstract, isExtern, attrsH, bodyH);
        hamuts.addFunction(header.toPrototype, functionH)

        (temporaryFunctionRefH)
      }
    }
  }

  def translateFunctionAttributes(attributes: Vector[IFunctionAttributeT]) = {
    attributes.map({
      case UserFunctionT => UserFunctionH
      case PureT => PureH
      case ExternT(_) => vwat() // Should have been filtered out, hammer cares about extern directly
      case x => vimpl(x.toString)
    })
  }

  def translateFunctionRef(
      hinputs: Hinputs,
      hamuts: HamutsBox,
    currentFunctionHeader: FunctionHeaderT,
      prototype2: PrototypeT):
  (FunctionRefH) = {
    val (prototypeH) = typeHammer.translatePrototype(hinputs, hamuts, prototype2);
    val functionRefH = FunctionRefH(prototypeH);
    (functionRefH)
  }
}